"""Ingest plaintext tokens from plugin config into the encrypted vault."""

import re
from copy import deepcopy

from .vault import Vault

_GITHUB_URL_RE = re.compile(r"^(?:https?://)?(?:www\.)?github\.com/([^/?#]+)/([^/?#]+)")


def normalize_default_repo(value: str) -> str:
    """Normalize default_repo to `owner/repo`.

    Accepts a full GitHub URL (https://github.com/owner/repo[.git][/...])
    or an already-normalized `owner/repo`; strips scheme, host, trailing
    slash and `.git` suffix.
    """
    repo = (value or "").strip()
    if not repo:
        return ""
    match = _GITHUB_URL_RE.match(repo)
    if match:
        repo = f"{match.group(1)}/{match.group(2).removesuffix('.git')}"
    return repo.rstrip("/")


def ingest_tokens(config: dict, vault: Vault) -> dict:
    """Move plaintext tokens out of config into vault.

    Returns a dict of config keys whose values should be replaced (usually
    with empty strings) and saved by the caller.
    """
    changes = {}
    shared = config.get("shared_token", "")
    if shared:
        vault.set_shared_token(shared)
        changes["shared_token"] = ""
    personal = config.get("personal_tokens") or []
    new_list = deepcopy(personal)
    dirty = False
    for item in new_list:
        name = (item.get("name") or "").strip()
        token = item.get("token") or ""
        if name and token:
            vault.set_personal_token(name, token)
            item["token"] = ""
            dirty = True
    if dirty:
        changes["personal_tokens"] = new_list
    return changes
