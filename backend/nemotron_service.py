"""
Calls nvidia/nvidia-nemotron-nano-9b-v2 for resume generation.
Uses OpenAI-compatible API (e.g. NVIDIA NIM) when NVIDIA_NEMOTRON_ENDPOINT is set.
Otherwise returns a template LaTeX so the app works without API keys.
"""
from pathlib import Path
from typing import Any, Optional

import httpx
from jinja2 import Environment, FileSystemLoader

from config import NVIDIA_NEMOTRON_API_KEY, NVIDIA_NEMOTRON_ENDPOINT
from models import GenerateResumeRequest


def _template_dir() -> str:
    return str(Path(__file__).resolve().parent / "templates")


def _render_prompt(req: GenerateResumeRequest) -> str:
    env = Environment(loader=FileSystemLoader(_template_dir()))
    t = env.get_template("resume_prompt.txt")
    return t.render(
        name=req.profile.name,
        major=req.profile.major or "N/A",
        age=req.profile.age,
        cgpa=req.profile.cgpa or "",
        show_age=req.profile.show_age,
        show_cgpa=req.profile.show_cgpa,
        github_repos=req.github_repos or [],
        linkedin_text="(N/A — profile + GitHub + job only)",
        job_description=req.job.job_description or req.job.job_url or "(Not provided)",
        good_to_have=req.good_to_have.text if req.good_to_have else "(Not provided)",
    )


def _fallback_latex(req: GenerateResumeRequest) -> str:
    """When no Nemotron endpoint: return a valid LaTeX resume from inputs."""
    name = req.profile.name or "Your Name"
    major = req.profile.major or "Your Major"
    lines = [
        r"\documentclass[11pt,a4paper]{article}",
        r"\usepackage[margin=0.75in]{geometry}",
        r"\usepackage{enumitem}",
        r"\setlength{\parindent}{0pt}",
        r"\title{}",
        r"\date{}",
        r"\begin{document}",
        r"\begin{center}",
        f"{{\\Large \\textbf{{{name}}}}}\\\\[0.3em]",
        f"{major}",
        r"\end{center}",
        r"\vspace{0.5em}",
        r"\section*{Education}",
        f"\\textbf{{{major}}}",
        r"\section*{Projects}",
    ]
    for repo in (req.github_repos or [])[:5]:
        desc = repo.description or "Project"
        lines.append(f"\\textbf{{{repo.name}}} --- {desc}")
    lines.append(r"\section*{Skills}")
    lines.append("(Tailor to job when Nemotron API is connected)")
    lines.append(r"\end{document}")
    return "\n".join(lines)


async def generate_latex(req: GenerateResumeRequest) -> tuple[str, Optional[str]]:
    """
    Returns (latex_content, error_message).
    If error_message is set, latex_content may be fallback or empty.
    """
    prompt = _render_prompt(req)
    endpoint = (NVIDIA_NEMOTRON_ENDPOINT or "").strip()
    if not endpoint:
        return _fallback_latex(req), None
    url = endpoint.rstrip("/")
    if "/v1/chat/completions" not in url:
        url = f"{url}/v1/chat/completions" if not url.endswith("/") else f"{url}v1/chat/completions"
    payload: dict[str, Any] = {
        "model": "nvidia/nvidia-nemotron-nano-9b-v2",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.3,
    }
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if NVIDIA_NEMOTRON_API_KEY:
        headers["Authorization"] = f"Bearer {NVIDIA_NEMOTRON_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return _fallback_latex(req), f"Nemotron API error: {e!s}"
    choice = (data.get("choices") or [None])[0]
    if not choice:
        return _fallback_latex(req), "No response from model"
    content = (choice.get("message") or {}).get("content") or ""
    latex = _extract_latex(content)
    if not latex.strip():
        return _fallback_latex(req), "Model did not return valid LaTeX"
    return latex, None


def _extract_latex(content: str) -> str:
    """Extract \\documentclass ... \\end{document} from model output."""
    content = content.strip()
    start = content.find(r"\documentclass")
    if start == -1:
        return content
    end = content.find(r"\end{document}")
    if end == -1:
        return content[start:]
    return content[start : end + len(r"\end{document}")]
