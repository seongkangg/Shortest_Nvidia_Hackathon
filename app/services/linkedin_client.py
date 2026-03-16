from typing import Any, Dict
import httpx
from app.models import LinkedInProfile


LINKEDIN_API = "https://api.linkedin.com/v2"


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
