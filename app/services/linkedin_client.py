from __future__ import annotations
from typing import Any, Dict, List
import json
import re
from bs4 import BeautifulSoup
import httpx
from app.models import LinkedInProfile


LINKEDIN_API = "https://api.linkedin.com/v2"
LINKEDIN_PROFILE_RE = re.compile(r"^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?", re.IGNORECASE)
DATE_RANGE_RE = re.compile(
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+\d{4}\s*-\s*(?:present|current|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+\d{4}|\d{4})",
    re.IGNORECASE,
)
GENERIC_SECTION_HEADERS = {
    "experience",
    "education",
    "skills",
    "licenses & certifications",
    "projects",
    "honors & awards",
    "volunteer experience",
    "publications",
}


async def fetch_profile(token: str) -> LinkedInProfile:
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        basic_resp = await client.get(
            f"{LINKEDIN_API}/userinfo",
            headers=headers,
        )
        if basic_resp.status_code != 200:
            # Fallback shape for restricted APIs; return minimal profile.
            return LinkedInProfile(full_name="LinkedIn User")
        data: Dict[str, Any] = basic_resp.json()
        full_name = data.get("name") or " ".join(
            [x for x in [data.get("given_name"), data.get("family_name")] if x]
        ).strip()
        return LinkedInProfile(
            full_name=full_name or None,
            headline=data.get("headline"),
            summary=data.get("locale"),
            experiences=[],
            education=[],
            skills=[],
            certifications=[],
        )


def normalize_profile_url(profile_url: str) -> str:
    raw = (profile_url or "").strip()
    if not raw:
        raise ValueError("LinkedIn profile URL is required.")
    if not raw.startswith("http://") and not raw.startswith("https://"):
        raw = f"https://{raw}"
    if not LINKEDIN_PROFILE_RE.match(raw):
        raise ValueError("LinkedIn profile URL must look like https://www.linkedin.com/in/<handle>.")
    return raw.split("?", 1)[0].rstrip("/")


async def fetch_profile_from_url(profile_url: str) -> LinkedInProfile:
    normalized = normalize_profile_url(profile_url)
    html = await _fetch_profile_html(normalized)
    parsed = _parse_public_profile_html(html)

    # Ensure at least a minimally useful profile.
    if not parsed.full_name:
        slug = normalized.rsplit("/", 1)[-1].replace("-", " ").strip()
        parsed.full_name = slug.title() if slug else "LinkedIn User"
    return parsed


async def _fetch_profile_html(profile_url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
        resp = await client.get(profile_url, headers=headers)
        resp.raise_for_status()
        html = resp.text

        # Public LinkedIn pages are often restricted. Fallback through r.jina.ai to obtain readable content.
        if not html or "authwall" in html.lower() or "sign in" in html.lower():
            fallback = await client.get(f"https://r.jina.ai/http://{profile_url.removeprefix('https://')}", headers=headers)
            if fallback.status_code < 400 and fallback.text:
                return fallback.text
        return html


def _parse_public_profile_html(html: str) -> LinkedInProfile:
    soup = BeautifulSoup(html, "html.parser")
    full_name = _extract_name(soup)
    headline = _extract_headline(soup)
    summary = _extract_summary(soup)

    experiences = _extract_experience_from_ld_json(soup)
    if not experiences:
        experiences = _extract_experience_from_sections(soup)

    return LinkedInProfile(
        full_name=full_name,
        headline=headline,
        summary=summary,
        experiences=experiences,
        education=[],
        skills=[],
        certifications=[],
    )


def _extract_name(soup: BeautifulSoup) -> str | None:
    for selector in ("h1", "title"):
        el = soup.select_one(selector)
        if not el:
            continue
        text = _clean_text(el.get_text(" ", strip=True))
        if not text:
            continue
        if selector == "title":
            text = text.split("|")[0].strip()
        if len(text.split()) >= 2:
            return text
    return None


def _extract_headline(soup: BeautifulSoup) -> str | None:
    meta_desc = soup.select_one('meta[name="description"]')
    if meta_desc and meta_desc.get("content"):
        return _clean_text(meta_desc["content"])[:220]

    og_title = soup.select_one('meta[property="og:title"]')
    if og_title and og_title.get("content"):
        title = _clean_text(og_title["content"])
        parts = [p.strip() for p in title.split("|")]
        if len(parts) > 1:
            return parts[1][:220]
    return None


def _extract_summary(soup: BeautifulSoup) -> str | None:
    for heading in soup.find_all(["h2", "h3"]):
        label = _clean_text(heading.get_text(" ", strip=True)).lower()
        if label in {"about", "summary"}:
            parent_text = _clean_text(heading.parent.get_text(" ", strip=True))
            if parent_text and len(parent_text) > len(label) + 10:
                return parent_text[:1200]
    return None


def _extract_experience_from_ld_json(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        objects = data if isinstance(data, list) else [data]
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            works_for = obj.get("worksFor")
            if isinstance(works_for, list):
                for role in works_for:
                    if isinstance(role, dict):
                        name = _clean_text(role.get("name", ""))
                        if name:
                            results.append({"title": None, "company": name})
            elif isinstance(works_for, dict):
                name = _clean_text(works_for.get("name", ""))
                if name:
                    results.append({"title": None, "company": name})
    return _dedupe_experiences(results)


def _extract_experience_from_sections(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    text = soup.get_text("\n", strip=True)
    lines = [_clean_text(line) for line in text.splitlines() if _clean_text(line)]
    if not lines:
        return []

    start = _find_section_index(lines, "experience")
    if start < 0:
        return []
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].lower() in GENERIC_SECTION_HEADERS and lines[idx].lower() != "experience":
            end = idx
            break

    section_lines = lines[start + 1 : end]
    experiences: List[Dict[str, Any]] = []
    i = 0
    while i < len(section_lines):
        line = section_lines[i]
        if DATE_RANGE_RE.search(line):
            company = section_lines[i - 1] if i - 1 >= 0 else None
            title = section_lines[i - 2] if i - 2 >= 0 else None
            desc_candidates = section_lines[i + 1 : i + 3]
            description = " ".join(x for x in desc_candidates if x and len(x.split()) > 3)[:500]
            experiences.append(
                {
                    "title": title,
                    "company": company,
                    "date_range": line,
                    "description": description or None,
                }
            )
        i += 1

    return _dedupe_experiences(experiences)


def _find_section_index(lines: List[str], section: str) -> int:
    section_lower = section.lower()
    for idx, line in enumerate(lines):
        if line.lower() == section_lower:
            return idx
    return -1


def _dedupe_experiences(experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    seen = set()
    for exp in experiences:
        title = _clean_text(str(exp.get("title") or ""))
        company = _clean_text(str(exp.get("company") or ""))
        date_range = _clean_text(str(exp.get("date_range") or ""))
        key = (title.lower(), company.lower(), date_range.lower())
        if key == ("", "", "") or key in seen:
            continue
        seen.add(key)
        cleaned.append(
            {
                "title": title or None,
                "company": company or None,
                "date_range": date_range or None,
                "description": _clean_text(str(exp.get("description") or "")) or None,
            }
        )
    return cleaned[:12]


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()
