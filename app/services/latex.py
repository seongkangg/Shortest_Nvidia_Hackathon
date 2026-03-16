from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import base64
import subprocess
import tempfile
from app.models import GithubRepo, LinkedInProfile, UserProfile


def latex_escape(value: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(ch, ch) for ch in (value or ""))


def render_resume_latex(
    profile: UserProfile,
    job: Dict[str, Any],
    repos: List[GithubRepo],
    linkedin_profile: LinkedInProfile,
    ai_content: Dict[str, Any],
) -> str:
    summary = latex_escape(ai_content.get("summary", ""))
    project_bullets = ai_content.get("project_bullets", [])
    exp_bullets = ai_content.get("experience_bullets", [])
    skills = ai_content.get("skills", [])

    edu_lines: List[str] = []
    if profile.major:
        edu_line = profile.major
        if profile.cgpa:
            edu_line += f" | CGPA: {profile.cgpa}"
        edu_lines.append(edu_line)
    for edu in linkedin_profile.education[:2]:
        school = edu.get("school", "")
        degree = edu.get("degree", "")
        if school or degree:
            edu_lines.append(f"{degree} - {school}".strip(" -"))

    contact_bits = [profile.email, profile.phone, profile.location]
    if profile.linkedin_url:
        contact_bits.append(profile.linkedin_url)
    if profile.github_url:
        contact_bits.append(profile.github_url)
    contact = " | ".join([latex_escape(x) for x in contact_bits if x])

    projects_section = "\n".join([f"\\item {latex_escape(p)}" for p in project_bullets[:6]])
    if not projects_section:
        projects_section = "\n\\item No project bullets generated."

    exp_section = "\n".join([f"\\item {latex_escape(e)}" for e in exp_bullets[:6]])
    if not exp_section:
        exp_section = "\n\\item No experience bullets generated."

    skill_line = ", ".join([latex_escape(s) for s in skills[:20]])
    edu_section = "\n".join([f"\\item {latex_escape(e)}" for e in edu_lines]) or "\\item Not provided."

    role = latex_escape(job.get("role_title") or "Target Role")
    good_to_have_line = ", ".join([latex_escape(x) for x in profile.good_to_have]) or "N/A"

    return rf"""\documentclass[11pt]{{article}}
\usepackage[margin=0.7in]{{geometry}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{enumitem}}
\setlist[itemize]{{leftmargin=1.2em, itemsep=2pt, topsep=2pt}}
\pagenumbering{{gobble}}
\begin{{document}}

\begin{{center}}
{{\LARGE \textbf{{{latex_escape(profile.name)}}}}}\\
{contact}
\end{{center}}

\section*{{Target}}
{role}

\section*{{Profile Summary}}
{summary}

\section*{{Education}}
\begin{{itemize}}
{edu_section}
\end{{itemize}}

\section*{{Experience}}
\begin{{itemize}}
{exp_section}
\end{{itemize}}

\section*{{Projects}}
\begin{{itemize}}
{projects_section}
\end{{itemize}}

\section*{{Skills}}
{skill_line}

\section*{{Good To Have Focus}}
{good_to_have_line}

\end{{document}}
"""


def compile_latex_to_pdf_base64(latex: str) -> tuple[bool, str, str | None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "resume.tex"
        pdf_path = Path(tmpdir) / "resume.pdf"
        tex_path.write_text(latex, encoding="utf-8")

        cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", str(tex_path)]
        try:
            subprocess.run(
                cmd,
                cwd=tmpdir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=40,
            )
        except FileNotFoundError:
            return False, "pdflatex not installed on this machine.", None
        except subprocess.CalledProcessError as e:
            snippet = (e.stdout or "")[-2000:]
            return False, f"LaTeX compile failed. Log:\n{snippet}", None
        except subprocess.TimeoutExpired:
            return False, "LaTeX compile timed out.", None

        if not pdf_path.exists():
            return False, "PDF not produced by pdflatex.", None

        raw = pdf_path.read_bytes()
        encoded = base64.b64encode(raw).decode("utf-8")
        return True, "Compilation successful.", encoded
