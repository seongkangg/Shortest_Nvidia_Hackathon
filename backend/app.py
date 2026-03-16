from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from config import APP_BASE_URL, API_BASE_URL, CORS_ORIGINS_EXTRA
from github_service import (
    exchange_github_code,
    fetch_repos,
    get_github_oauth_url,
    get_github_token,
    store_github_token,
)
from job_service import fetch_job_description
from models import (
    CreateResumeRequest,
    GenerateResumeRequest,
    GenerateResumeResponse,
    JobFetchRequest,
    JobFetchResponse,
    ReposResponse,
    ResumeDetail,
    ResumeListResponse,
    UpdateResumeRequest,
)
from nemotron_service import generate_latex
from resume_store import create_resume, get_resume, list_resumes, update_resume

app = FastAPI(title="Nemotron Resume Builder API")

# Allow localhost and file:// for local dev; add CORS_ORIGINS in .env for production (e.g. https://your-app.vercel.app)
_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "null",
] + CORS_ORIGINS_EXTRA
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Health -----
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ----- GitHub OAuth -----
@app.get("/auth/github")
async def github_auth():
    url, state = get_github_oauth_url()
    return {"auth_url": url, "state": state}


@app.get("/auth/github/callback")
async def github_callback(
    code: str = Query(..., alias="code"),
    state: str = Query(..., alias="state"),
):
    token = await exchange_github_code(code, state)
    if token:
        store_github_token(state, token)
    # Redirect to frontend with state so it can call GET /repos
    frontend = APP_BASE_URL.rstrip("/")
    return RedirectResponse(url=f"{frontend}/?github_state={state}")


@app.get("/repos", response_model=ReposResponse)
async def list_github_repos(
    state: str | None = Query(None, alias="state"),
    authorization: str | None = None,
):
    token = get_github_token(state) if state else None
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    if not token:
        return ReposResponse(repos=[], connected=False)
    repos = await fetch_repos(token)
    return ReposResponse(repos=repos, connected=True)


# ----- Job description fetch -----
@app.post("/job/fetch", response_model=JobFetchResponse)
async def job_fetch(body: JobFetchRequest):
    result = await fetch_job_description(body.job_url, body.job_description)
    return result


# ----- Generate resume (Nemotron) -----
@app.post("/generate-resume", response_model=GenerateResumeResponse)
async def generate_resume(body: GenerateResumeRequest):
    latex, err = await generate_latex(body)
    if err:
        return GenerateResumeResponse(latex=latex, error=err)
    # Optionally save first version
    detail = create_resume(
        latex,
        job_url=body.job.job_url,
        job_title=body.job.job_description[:80] if body.job.job_description else None,
    )
    return GenerateResumeResponse(latex=latex, resume_id=detail.id)


# ----- Resume CRUD (save / edit later) -----
@app.get("/resumes", response_model=ResumeListResponse)
async def resume_list():
    metas = list_resumes()
    return ResumeListResponse(resumes=metas)


@app.get("/resumes/{resume_id}", response_model=ResumeDetail)
async def resume_get(resume_id: str):
    r = get_resume(resume_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resume not found")
    return r


@app.put("/resumes/{resume_id}", response_model=ResumeDetail)
async def resume_update(resume_id: str, body: UpdateResumeRequest):
    r = update_resume(resume_id, title=body.title, latex=body.latex)
    if not r:
        raise HTTPException(status_code=404, detail="Resume not found")
    return r


@app.post("/resumes", response_model=ResumeDetail)
async def resume_create(body: CreateResumeRequest):
    detail = create_resume(
        body.latex,
        title=body.title,
        job_url=body.job_url,
        job_title=body.job_title,
    )
    return detail
