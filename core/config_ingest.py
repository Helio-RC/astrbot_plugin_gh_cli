"""Ingest plaintext tokens from plugin config into the encrypted vault."""

from copy import deepcopy

from .vault import Vault


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
