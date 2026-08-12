"""/gh command parser: shlex-based, gh-CLI-like syntax."""

import shlex
from typing import Any

from .operations import registry

_HELP_PREFIX = (
    "GitHub CLI 插件\n"
    "用法: /gh <指令组> <操作> [参数]\n"
    "通用参数: -R owner/repo 指定仓库（缺省用配置的 default_repo）\n"
    "身份: /gh auth use <名称> 切换个人 Token；/gh auth status 查看身份\n"
)

_KNOWN_BOOL_FLAGS = {"private", "public", "draft", "prerelease"}


def parse_args(tokens: list[str]) -> dict[str, Any]:
    """Parse tokens into a params dict.

    -R <repo> or --repo <repo> -> params["repo"]
    --flag value / --flag=value -> params["flag"] = value
    boolean flags (--private etc.) -> params["flag"] = True
    positional args -> params["pos"] list
    """
    params: dict[str, Any] = {"pos": []}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "-R" or tok == "--repo":
            i += 1
            if i >= len(tokens):
                raise ValueError(f"{tok} 缺少参数值。")
            params["repo"] = tokens[i]
        elif tok.startswith("--") and "=" in tok:
            key, _, value = tok[2:].partition("=")
            if key in _KNOWN_BOOL_FLAGS:
                params[key] = value.lower() in ("true", "1", "yes", "on")
            else:
                params[key] = value
        elif tok.startswith("--"):
            key = tok[2:]
            if key in _KNOWN_BOOL_FLAGS:
                params[key] = True
            else:
                i += 1
                if i >= len(tokens):
                    raise ValueError(f"--{key} 缺少参数值。")
                params[key] = tokens[i]
        elif tok.startswith("-") and len(tok) > 1:
            raise ValueError(f"不支持的参数: {tok}。长参数请用 --flag 形式。")
        else:
            params["pos"].append(tok)
        i += 1
    return params


def parse_command(text: str) -> tuple[str, str, dict]:
    """'issue list -R o/r --state all' -> ('issue', 'list', {...})."""
    tokens = shlex.split(text)
    if not tokens:
        raise ValueError("请输入指令，例如 /gh repo view。")
    group = tokens[0]
    action = tokens[1] if len(tokens) > 1 else ""
    rest = tokens[2:] if len(tokens) > 1 else []
    params = parse_args(rest)
    return group, action, params


def build_help() -> str:
    lines = [_HELP_PREFIX.strip(), ""]
    for name in sorted(registry._GROUPS):
        mod = registry.get_group(name)
        lines.append(mod.HELP)
        lines.append("")
    return "\n".join(lines)
