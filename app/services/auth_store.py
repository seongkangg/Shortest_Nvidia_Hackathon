from typing import Dict, Optional


class InMemoryTokenStore:
    def __init__(self) -> None:
        self._github_tokens: Dict[str, str] = {}
        self._linkedin_tokens: Dict[str, str] = {}

    def set_github_token(self, session_id: str, token: str) -> None:
        self._github_tokens[session_id] = token

    def get_github_token(self, session_id: str) -> Optional[str]:
        return self._github_tokens.get(session_id)

    def set_linkedin_token(self, session_id: str, token: str) -> None:
        self._linkedin_tokens[session_id] = token

    def get_linkedin_token(self, session_id: str) -> Optional[str]:
        return self._linkedin_tokens.get(session_id)


token_store = InMemoryTokenStore()
