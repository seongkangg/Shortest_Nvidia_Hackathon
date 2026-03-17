from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field


class UserProfile(BaseModel):
    name: str
    age: Optional[int] = None
    major: Optional[str] = None
    cgpa: Optional[str] = None
    good_to_have: List[str] = Field(default_factory=list)
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class GithubRepo(BaseModel):
    name: str
    description: Optional[str] = None
    html_url: str
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    stargazers_count: int = 0
    forks_count: int = 0
    updated_at: Optional[str] = None
    readme_excerpt: Optional[str] = None


class LinkedInProfile(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    experiences: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)


class GenerateResumeRequest(BaseModel):
    session_id: str
    profile: UserProfile
    job_url: Optional[HttpUrl] = None
    job_description: Optional[str] = None
    github_token: Optional[str] = None
    include_readme: bool = False
    selected_repo_names: List[str] = Field(default_factory=list)


class GenerateResumeResponse(BaseModel):
    latex: str
    parsed_job: Dict[str, Any]
    github_repos: List[GithubRepo]
    linkedin_profile: LinkedInProfile
    warnings: List[str] = Field(default_factory=list)


class CompileLatexRequest(BaseModel):
    latex: str


class CompileLatexResponse(BaseModel):
    success: bool
    message: str
    pdf_base64: Optional[str] = None
