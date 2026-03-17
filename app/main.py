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


@app.get("/api/github/repos", response_model=List[GithubRepo])
async def github_repos(session_id: str, include_readme: bool = False, token: str | None = None) -> List[GithubRepo]:
    gh_token = token or token_store.get_github_token(session_id)
    if not gh_token:
        raise HTTPException(status_code=400, detail="Missing GitHub token. Paste a token above or connect via OAuth.")
    try:
        return await list_repos(gh_token, include_readme=include_readme)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {e}") from e


@app.post("/api/generate", response_model=GenerateResumeResponse)
async def generate_resume(payload: GenerateResumeRequest) -> GenerateResumeResponse:
    warnings: List[str] = []

    job_description = payload.job_description
    if payload.job_url and not job_description:
        try:
            job_description = await fetch_job_description(str(payload.job_url))
        except Exception as e:
            warnings.append(f"Unable to fetch job URL. Paste job description manually. Error: {e}")
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
        warnings.append("No GitHub token: project section will be thin. Paste a GitHub token in Integrations.")

    # No LinkedIn: experience bullets come from profile + GitHub + LLM
    linkedin_profile_data = LinkedInProfile(full_name=payload.profile.name)

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
