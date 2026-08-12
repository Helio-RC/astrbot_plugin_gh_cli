"""Operation dispatch registry. Each group module registers MODE/WRITE/HANDLERS."""

import asyncio
from collections.abc import Callable
from typing import Any

from ..client import GhClient

MODE = "sync"
WRITE: set[str] = set()
HANDLERS: dict[str, Callable] = {}

_GROUPS: dict[str, Any] = {}


def register_group(name: str, module: Any) -> None:
    _GROUPS[name] = module


def get_group(name: str) -> Any:
    try:
        return _GROUPS[name]
    except KeyError:
        raise KeyError(f"不支持的指令组: {name}")


async def run(client: GhClient, group: str, action: str, params: dict) -> Any:
    mod = get_group(group)
    if action not in mod.HANDLERS:
        raise KeyError(f"指令组 {group} 不支持该操作: {action}")
    handler = mod.HANDLERS[action]
    if mod.MODE == "sync":
        return await asyncio.to_thread(handler, client, params)
    return await handler(client, params)


from . import repo as _repo

register_group("repo", _repo)


from . import issue as _issue

register_group("issue", _issue)


from . import pr as _pr

register_group("pr", _pr)


from . import release as _release

register_group("release", _release)


from . import gist as _gist

register_group("gist", _gist)


from . import search as _search

register_group("search", _search)


from . import run as _run

register_group("run", _run)


from . import api as _api

register_group("api", _api)
