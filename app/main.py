from __future__ import annotations
from typing import Any, Dict, List
import urllib.parse
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models import (
    CompileLatexRequest,
    CompileLatexResponse,
    GenerateResumeRequest,
    GenerateResumeResponse,
    GithubRepo,
    LinkedInProfile,
)
from app.services.auth_store import token_store
from app.services.github_client import list_repos
from app.services.job_parser import extract_job_structure, fetch_job_description
from app.services.latex import compile_latex_to_pdf_base64, render_resume_latex
from app.services.linkedin_client import fetch_profile, fetch_profile_from_url
from app.services.llm import tailor_resume_content


settings = get_settings()

app = FastAPI(title="Resume Builder API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def home() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/auth/github/url")
async def github_auth_url(session_id: str = Query(...), redirect_uri: str = Query(...)) -> Dict[str, str]:
    if not settings.github_client_id:
        raise HTTPException(status_code=400, detail="GITHUB_CLIENT_ID not configured.")
    params = urllib.parse.urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user repo",
            "state": session_id,
        }
    )
    return {"url": f"https://github.com/login/oauth/authorize?{params}"}


@app.get("/api/auth/github/callback")
async def github_callback(code: str = Query(...), state: str = Query(...)) -> Dict[str, str]:
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=400, detail="GitHub OAuth not fully configured.")
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise HTTPException(status_code=400, detail="No GitHub access token received.")
        token_store.set_github_token(state, token)
        return {"message": "GitHub connected."}


@app.get("/api/auth/linkedin/url")
async def linkedin_auth_url(session_id: str = Query(...), redirect_uri: str = Query(...)) -> Dict[str, str]:
    if not settings.linkedin_client_id:
        raise HTTPException(status_code=400, detail="LINKEDIN_CLIENT_ID not configured.")
    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": settings.linkedin_client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
            "state": session_id,
        }
    )
    return {"url": f"https://www.linkedin.com/oauth/v2/authorization?{params}"}


@app.get("/api/auth/linkedin/callback")
async def linkedin_callback(code: str = Query(...), state: str = Query(...), redirect_uri: str = Query(...)) -> Dict[str, str]:
    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        raise HTTPException(status_code=400, detail="LinkedIn OAuth not fully configured.")
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.linkedin_client_id,
                "client_secret": settings.linkedin_client_secret,
            },
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise HTTPException(status_code=400, detail="No LinkedIn access token received.")
        token_store.set_linkedin_token(state, token)
        return {"message": "LinkedIn connected."}


@app.get("/api/github/repos", response_model=List[GithubRepo])
async def github_repos(session_id: str, include_readme: bool = False, token: str | None = None) -> List[GithubRepo]:
    gh_token = token or token_store.get_github_token(session_id)
    if not gh_token:
        raise HTTPException(status_code=400, detail="Missing GitHub token. Connect account or provide token.")
    try:
        return await list_repos(gh_token, include_readme=include_readme)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {e}") from e


@app.get("/api/linkedin/profile", response_model=LinkedInProfile)
async def linkedin_profile(
    session_id: str | None = None,
    token: str | None = None,
    profile_url: str | None = None,
) -> LinkedInProfile:
    if profile_url:
        try:
            return await fetch_profile_from_url(profile_url)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LinkedIn profile scrape error: {e}") from e

    li_token = token or (token_store.get_linkedin_token(session_id) if session_id else None)
    if not li_token:
        raise HTTPException(
            status_code=400,
            detail="Provide LinkedIn profile_url or token (or connect via OAuth).",
        )
    try:
        return await fetch_profile(li_token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LinkedIn API error: {e}") from e


@app.post("/api/generate", response_model=GenerateResumeResponse)
async def generate_resume(payload: GenerateResumeRequest) -> GenerateResumeResponse:
    warnings: List[str] = []

    job_description = payload.job_description
    if payload.job_url and not job_description:
        try:
            job_description = await fetch_job_description(str(payload.job_url))
        except Exception as e:
            warnings.append(f"Unable to fetch job URL. Please paste job description manually. Error: {e}")
            job_description = ""
    parsed_job = extract_job_structure(job_description or "")

    repos: List[GithubRepo] = []
    gh_token = payload.github_token or token_store.get_github_token(payload.session_id)
    if gh_token:
        try:
            repos = await list_repos(gh_token, include_readme=payload.include_readme)
            if payload.selected_repo_names:
                selected = set(payload.selected_repo_names)
                repos = [r for r in repos if r.name in selected]
        except Exception as e:
            warnings.append(f"GitHub data could not be fetched: {e}")
    else:
        warnings.append("No GitHub token found. Project section may be limited.")

    linkedin_profile_data = payload.linkedin_profile_override
    profile_url = str(payload.linkedin_profile_url or payload.profile.linkedin_url or "").strip()
    li_token = payload.linkedin_token or token_store.get_linkedin_token(payload.session_id)
    if not linkedin_profile_data and profile_url:
        try:
            linkedin_profile_data = await fetch_profile_from_url(profile_url)
        except Exception as e:
            warnings.append(f"LinkedIn profile URL could not be scraped: {e}")
    if not linkedin_profile_data and li_token:
        try:
            linkedin_profile_data = await fetch_profile(li_token)
        except Exception as e:
            warnings.append(f"LinkedIn data could not be fetched: {e}")
    if not linkedin_profile_data:
        linkedin_profile_data = LinkedInProfile(full_name=payload.profile.name)
        warnings.append("No LinkedIn profile available; using minimal profile.")

    ai_content = await tailor_resume_content(payload.profile, parsed_job, repos, linkedin_profile_data)
    latex = render_resume_latex(payload.profile, parsed_job, repos, linkedin_profile_data, ai_content)

    return GenerateResumeResponse(
        latex=latex,
        parsed_job=parsed_job,
        github_repos=repos,
        linkedin_profile=linkedin_profile_data,
        warnings=warnings,
    )


@app.post("/api/compile", response_model=CompileLatexResponse)
async def compile_latex(payload: CompileLatexRequest) -> CompileLatexResponse:
    success, message, pdf_base64 = compile_latex_to_pdf_base64(payload.latex)
    return CompileLatexResponse(success=success, message=message, pdf_base64=pdf_base64)
