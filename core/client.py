"""GitHub client factory and raw REST helper."""

import logging
from typing import Any
from urllib.parse import urlparse

import aiohttp
from github import Auth, Github

from .vault import Vault

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GhError(Exception):
    """User-facing GitHub error; message is safe to show to chat users."""


class AuthError(GhError):
    pass


class GhClient:
    def __init__(self, vault: Vault, user_key: str | None = None) -> None:
        self.vault = vault
        self.user_key = user_key

    def resolve_token(self) -> str | None:
        if self.user_key:
            binding = self.vault.get_binding(self.user_key)
            if binding:
                token = self.vault.get_personal_token(binding)
                if token:
                    return token
        return self.vault.get_shared_token()

    def get_github(self) -> Github:
        token = self.resolve_token()
        if not token:
            raise AuthError("尚未配置 GitHub Token，请管理员在插件配置中填写。")
        return Github(auth=Auth.Token(token))

    async def rest(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        body: dict | None = None,
    ) -> tuple[int, Any]:
        token = self.resolve_token()
        if not token:
            raise AuthError("尚未配置 GitHub Token，请管理员在插件配置中填写。")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        url = path if path.startswith("http") else GITHUB_API_BASE + path
        parsed = urlparse(url)
        if parsed.hostname and parsed.hostname != "api.github.com":
            raise ValueError("仅允许调用 GitHub API（api.github.com）。")
        async with (
            aiohttp.ClientSession(headers=headers) as session,
            session.request(method, url, params=params, json=body) as resp,
        ):
            text = await resp.text()
            try:
                data = await resp.json()
            except (ValueError, aiohttp.ContentTypeError):
                data = text
            return resp.status, data
