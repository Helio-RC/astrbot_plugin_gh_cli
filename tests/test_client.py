from pathlib import Path

import pytest

from core.client import AuthError, GhClient
from core.vault import Vault


def _client(tmp_path: Path, user_key: str | None = None) -> GhClient:
    return GhClient(Vault(tmp_path / "data"), user_key=user_key)


def test_resolve_falls_back_to_shared(tmp_path):
    c = _client(tmp_path)
    c.vault.set_shared_token("ghp_shared")
    assert c.resolve_token() == "ghp_shared"


def test_resolve_prefers_personal(tmp_path):
    c = _client(tmp_path, user_key="tg:1")
    c.vault.set_shared_token("ghp_shared")
    c.vault.set_personal_token("alice", "ghp_alice")
    c.vault.set_binding("tg:1", "alice")
    assert c.resolve_token() == "ghp_alice"


def test_resolve_unbound_user_falls_back_to_shared(tmp_path):
    c = _client(tmp_path, user_key="tg:999")
    c.vault.set_shared_token("ghp_shared")
    c.vault.set_personal_token("alice", "ghp_alice")
    c.vault.set_binding("tg:1", "alice")
    assert c.resolve_token() == "ghp_shared"


def test_resolve_none_when_unconfigured(tmp_path):
    assert _client(tmp_path).resolve_token() is None


def test_get_github_raises_without_token(tmp_path):
    with pytest.raises(AuthError):
        _client(tmp_path).get_github()


def test_get_github_creates_instance(tmp_path):
    c = _client(tmp_path)
    c.vault.set_shared_token("ghp_shared")
    g = c.get_github()
    assert g is not None


async def test_rest_rejects_external_host(tmp_path):
    c = _client(tmp_path)
    c.vault.set_shared_token("ghp_shared")
    with pytest.raises(ValueError):
        await c.rest("GET", "http://attacker.example/")
