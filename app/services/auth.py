import secrets
from collections.abc import Mapping

from app.utils.errors import AuthenticationError


class AuthService:
    def __init__(self, *, enabled: bool, api_key: str, exempt_paths: list[str]) -> None:
        self.enabled = enabled
        self.api_key = api_key
        self.exempt_paths = exempt_paths

    def authenticate(self, *, path: str, headers: Mapping[str, str]) -> None:
        if not self.enabled or self.is_exempt_path(path):
            return

        provided_key = self.extract_api_key(headers)
        if not provided_key or not secrets.compare_digest(provided_key, self.api_key):
            raise AuthenticationError()

    def is_exempt_path(self, path: str) -> bool:
        return path in self.exempt_paths

    @staticmethod
    def extract_api_key(headers: Mapping[str, str]) -> str | None:
        x_api_key = headers.get("x-api-key")
        if x_api_key:
            return x_api_key.strip() or None

        authorization = headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
            return token or None

        return None
