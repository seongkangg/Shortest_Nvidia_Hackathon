from typing import List
import base64
import httpx
from app.models import GithubRepo


GITHUB_API = "https://api.github.com"


async def list_repos(token: str, include_readme: bool = False) -> List[GithubRepo]:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{GITHUB_API}/user/repos?per_page=100&sort=updated", headers=headers)
        resp.raise_for_status()
        repos_raw = resp.json()

        repos: List[GithubRepo] = []
        for r in repos_raw:
            readme_excerpt = None
            if include_readme:
                readme_excerpt = await _fetch_readme_excerpt(client, headers, r["owner"]["login"], r["name"])
            repos.append(
                GithubRepo(
                    name=r["name"],
                    description=r.get("description"),
                    html_url=r["html_url"],
                    language=r.get("language"),
                    topics=r.get("topics", []),
                    stargazers_count=r.get("stargazers_count", 0),
                    forks_count=r.get("forks_count", 0),
                    updated_at=r.get("updated_at"),
                    readme_excerpt=readme_excerpt,
                )
            )
        return repos


async def _fetch_readme_excerpt(
    client: httpx.AsyncClient, headers: dict, owner: str, repo: str, max_len: int = 600
) -> str | None:
    try:
        resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/readme", headers=headers)
        if resp.status_code != 200:
            return None
        payload = resp.json()
        encoded = payload.get("content", "")
        if not encoded:
            return None
        decoded = base64.b64decode(encoded).decode("utf-8", errors="ignore")
        return decoded[:max_len]
    except Exception:
        return None
