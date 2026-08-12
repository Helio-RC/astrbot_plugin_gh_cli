"""api group: raw GitHub REST passthrough (async)."""

import json
from urllib.parse import urlparse

MODE = "async"
WRITE = {"POST", "PATCH", "PUT", "DELETE"}

HELP = (
    "原始 API:\n"
    "/gh api <path> [--method GET|POST|PATCH|PUT|DELETE] [--body JSON] [-R owner/repo]\n"
    "示例: /gh api /repos/octocat/Hello-World\n"
    '示例: /gh api /repos/octocat/Hello-World/issues --method POST --body \'{"title": "hi"}\''
)


def _parse_body(raw):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("--body 必须是合法 JSON。") from None


async def call(client, params):
    path = params.get("path", "").strip()
    if not path:
        raise ValueError("缺少 API 路径: /gh api <path>")
    if path.startswith("http"):
        parsed = urlparse(path)
        if parsed.hostname != "api.github.com":
            raise ValueError("仅允许调用 GitHub API（api.github.com）。")
    elif not path.startswith("/"):
        path = "/" + path
    method = (params.get("method") or "GET").upper()
    body = _parse_body(params.get("body"))
    status, data = await client.rest(
        method, path, params=params.get("query"), body=body
    )
    return {"status": status, "data": data, "ok": 200 <= status < 300}


def format(data, list_limit: int, content_limit: int) -> str:
    status = data["status"]
    icon = "✅" if data["ok"] else "⚠️"
    if data["ok"] and isinstance(data["data"], (dict, list)):
        try:
            text = json.dumps(data["data"], ensure_ascii=False, indent=2)
        except TypeError:
            text = str(data["data"])
    else:
        text = str(data["data"])
    text = text[:content_limit]
    if len(str(data["data"])) > content_limit:
        text += "…(已截断)"
    return f"{icon} HTTP {status}\n{text}"


HANDLERS = {"call": call}
