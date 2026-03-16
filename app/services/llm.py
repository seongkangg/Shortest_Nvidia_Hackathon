from __future__ import annotations
from typing import Any, Dict, List
import json
import httpx
from app.config import get_settings
from app.models import GithubRepo, LinkedInProfile, UserProfile


async def tailor_resume_content(
    profile: UserProfile,
    job: Dict[str, Any],
    repos: List[GithubRepo],
    linkedin_profile: LinkedInProfile,
) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.nvidia_api_base_url or not settings.nvidia_api_key:
        return _fallback_content(profile, job, repos, linkedin_profile)

    prompt_payload = {
        "profile": profile.model_dump(),
        "job": job,
        "repos": [r.model_dump() for r in repos[:8]],
        "linkedin": linkedin_profile.model_dump(),
    }
    system_prompt = (
        "You are an expert resume writer. Output ONLY JSON with keys: "
        "summary, project_bullets, experience_bullets, skills."
    )
    user_prompt = (
        "Tailor the resume data to the target role. Emphasize alignment with required skills and "
        "good-to-have traits. Keep project bullets concise and impact-focused. "
        f"Input JSON:\n{json.dumps(prompt_payload)}"
    )

    try:
        completion = await _chat_completion(system_prompt, user_prompt)
        parsed = _safe_json_parse(completion)
        if parsed:
            return parsed
    except Exception:
        pass

    return _fallback_content(profile, job, repos, linkedin_profile)


async def _chat_completion(system_prompt: str, user_prompt: str) -> str:
    settings = get_settings()
    url = f"{settings.nvidia_api_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.nemotron_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _safe_json_parse(value: str) -> Dict[str, Any] | None:
    value = value.strip()
    # Handle fenced JSON.
    if value.startswith("```"):
        value = value.strip("`")
        value = value.replace("json", "", 1).strip()
    try:
        obj = json.loads(value)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        return None
    return None


def _fallback_content(
    profile: UserProfile,
    job: Dict[str, Any],
    repos: List[GithubRepo],
    linkedin_profile: LinkedInProfile,
) -> Dict[str, Any]:
    project_bullets = []
    for repo in repos[:4]:
        tech = repo.language or "Software"
        desc = repo.description or "Built and maintained project features."
        project_bullets.append(f"{repo.name}: {desc} Stack: {tech}.")

    required = ", ".join(job.get("required_skills", [])[:8])
    good = ", ".join(profile.good_to_have[:6])
    summary = (
        f"{profile.name} is a candidate with strengths in {required or 'software development'}. "
        f"Focus areas include {good or 'problem solving and implementation'}."
    )

    exp_bullets = []
    for exp in linkedin_profile.experiences[:4]:
        title = exp.get("title", "Role")
        company = exp.get("company", "Company")
        exp_bullets.append(f"Delivered measurable contributions as {title} at {company}.")

    skills = linkedin_profile.skills[:20]
    if not skills:
        skills = job.get("required_skills", [])[:12]

    return {
        "summary": summary,
        "project_bullets": project_bullets,
        "experience_bullets": exp_bullets,
        "skills": skills,
    }
