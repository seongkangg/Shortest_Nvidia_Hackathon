from typing import Any, Optional

from pydantic import BaseModel, Field


# ----- Profile & inputs -----
class ProfileInput(BaseModel):
    name: str = Field(..., min_length=1, description="Full name")
    major: str = Field("", description="Major / field of study")
    age: Optional[int] = Field(None, ge=0, le=120)
    cgpa: Optional[str] = Field(None, description="e.g. 3.85/4.0")
    show_age: bool = Field(True, description="Include age in resume")
    show_cgpa: bool = Field(True, description="Include CGPA in resume")


class GoodToHaveInput(BaseModel):
    text: str = Field("", description="Good-to-have / preferences (bullet points or paragraph)")


class JobInput(BaseModel):
    job_url: Optional[str] = Field(None, description="URL to fetch job description from")
    job_description: Optional[str] = Field(None, description="Pasted job description (overrides fetch)")


# ----- GitHub -----
class RepoSummary(BaseModel):
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    url: str = ""


class GitHubConnectResponse(BaseModel):
    auth_url: str
    state: str


class ReposResponse(BaseModel):
    repos: list[RepoSummary]
    connected: bool = True


# ----- Generate resume -----
class GenerateResumeRequest(BaseModel):
    profile: ProfileInput
    job: JobInput
    good_to_have: GoodToHaveInput = Field(default_factory=GoodToHaveInput)
    github_repos: list[RepoSummary] = Field(default_factory=list)
    preferences: Optional[dict[str, Any]] = Field(None, description="e.g. tone, length")


class GenerateResumeResponse(BaseModel):
    latex: str
    resume_id: Optional[str] = None
    error: Optional[str] = None


# ----- Resume CRUD (save / edit later) -----
class ResumeMeta(BaseModel):
    id: str
    title: Optional[str] = None
    job_url: Optional[str] = None
    job_title: Optional[str] = None
    created_at: str
    updated_at: str


class ResumeDetail(BaseModel):
    id: str
    title: Optional[str] = None
    job_url: Optional[str] = None
    job_title: Optional[str] = None
    latex: str
    created_at: str
    updated_at: str


class ResumeListResponse(BaseModel):
    resumes: list[ResumeMeta]


class UpdateResumeRequest(BaseModel):
    title: Optional[str] = None
    latex: Optional[str] = None


class CreateResumeRequest(BaseModel):
    latex: str = Field(..., min_length=1)
    title: Optional[str] = None
    job_url: Optional[str] = None
    job_title: Optional[str] = None


# ----- Job fetch -----
class JobFetchRequest(BaseModel):
    job_url: Optional[str] = None
    job_description: Optional[str] = None


class JobFetchResponse(BaseModel):
    job_title: Optional[str] = None
    raw_text: str
    error: Optional[str] = None
