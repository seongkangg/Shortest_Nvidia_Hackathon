import os
import secrets
from typing import Optional

import httpx

from config import (
    API_BASE_URL,
    GITHUB_CALLBACK_PATH,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
)
from models import RepoSummary

# In-memory: state -> access_token (for demo; use Redis/DB in production)
_github_tokens: dict[str, str] = {}


def get_github_oauth_url() -> tuple[str, str]:
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": f"{API_BASE_URL.rstrip('/')}{GITHUB_CALLBACK_PATH}",
        "scope": "read:user user:email repo",
        "state": state,
    }
    q = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://github.com/login/oauth/authorize?{q}"
    return url, state


async def exchange_github_code(code: str, state: str) -> Optional[str]:
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return None
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{API_BASE_URL.rstrip('/')}{GITHUB_CALLBACK_PATH}",
                "state": state,
            },
        )
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        if token:
            _github_tokens[state] = token
        return token


def store_github_token(state: str, token: str) -> None:
    _github_tokens[state] = token


def get_github_token(state: str) -> Optional[str]:
    return _github_tokens.get(state)


# Optional: accept token in header for API calls (e.g. Authorization: Bearer <state_or_token>)
def get_token_from_state_or_header(state: Optional[str] = None, auth_header: Optional[str] = None) -> Optional[str]:
    if state and state in _github_tokens:
        return _github_tokens[state]
    if auth_header and auth_header.startswith("Bearer "):
        t = auth_header[7:].strip()
        if t in _github_tokens.values():
            return t
        return t  # could be raw token
    return None


async def fetch_repos(access_token: str) -> list[RepoSummary]:
    repos: list[RepoSummary] = []
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.github.com/user/repos",
            params={"sort": "updated", "per_page": 100},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if r.status_code != 200:
            return repos
        for item in r.json():
            repos.append(
                RepoSummary(
                    name=item.get("full_name", item.get("name", "")),
                    description=item.get("description"),
                    language=item.get("language"),
                    stars=int(item.get("stargazers_count", 0)),
                    url=item.get("html_url", ""),
                )
            )
    return repos
