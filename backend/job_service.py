import re
from typing import Optional

import httpx

from models import JobFetchResponse


async def fetch_job_description(job_url: Optional[str], pasted_text: Optional[str]) -> JobFetchResponse:
    if pasted_text and pasted_text.strip():
        title = _extract_title_from_text(pasted_text.strip())
        return JobFetchResponse(job_title=title, raw_text=pasted_text.strip())
    if not job_url or not job_url.strip():
        return JobFetchResponse(raw_text="", error="No URL or pasted description provided")
    url = job_url.strip()
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            html = r.text
    except Exception as e:
        return JobFetchResponse(raw_text="", error=f"Failed to fetch URL: {e!s}")
    text = _extract_text_from_html(html)
    if not text.strip():
        return JobFetchResponse(raw_text="", error="Could not extract text from page. Please paste the job description.")
    title = _extract_title_from_text(text) or _extract_title_from_html(html)
    return JobFetchResponse(job_title=title, raw_text=text)


def _extract_title_from_html(html: str) -> Optional[str]:
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip() or None
    return None


def _extract_title_from_text(text: str) -> Optional[str]:
    first_line = text.split("\n")[0].strip()
    if len(first_line) < 120 and first_line:
        return first_line
    return None


def _extract_text_from_html(html: str) -> str:
    # Remove script/style
    html = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html, flags=re.IGNORECASE)
    # Replace br/div/p with newlines
    html = re.sub(r"</(?:br|div|p|li|tr)[^>]*>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return text.strip()
