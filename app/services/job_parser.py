from typing import Dict, Any
import re
import httpx
from bs4 import BeautifulSoup


async def fetch_job_description(url: str) -> str:
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        return cleaned[:12000]


def extract_job_structure(raw_text: str) -> Dict[str, Any]:
    text = raw_text or ""
    role_title = _first_match(text, [r"(?im)^job title[:\s]+(.+)$", r"(?im)^title[:\s]+(.+)$"])
    company = _first_match(text, [r"(?im)^company[:\s]+(.+)$"])
    skills = _extract_bullets_near_heading(text, ["requirements", "skills", "qualifications"])
    responsibilities = _extract_bullets_near_heading(text, ["responsibilities", "what you will do"])
    good_to_have = _extract_bullets_near_heading(text, ["good to have", "preferred", "nice to have"])

    return {
        "role_title": role_title,
        "company_name": company,
        "required_skills": skills[:20],
        "responsibilities": responsibilities[:20],
        "good_to_have": good_to_have[:20],
        "raw_excerpt": text[:3000],
    }


def _first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1).strip()
    return None


def _extract_bullets_near_heading(text: str, heading_keywords: list[str]) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    out: list[str] = []
    for idx, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in heading_keywords):
            window = lines[idx + 1 : idx + 12]
            for w in window:
                if len(w) < 3:
                    continue
                if w.startswith(("-", "*", "•")):
                    out.append(w.lstrip("-*• ").strip())
                elif re.match(r"^\d+\.", w):
                    out.append(re.sub(r"^\d+\.\s*", "", w).strip())
    deduped = []
    seen = set()
    for item in out:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped
