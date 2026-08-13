"""gist group: list / view / create / edit / comment / delete."""

from github import InputFileContent

MODE = "sync"
WRITE = {"create", "edit", "delete", "comment"}

HELP = (
    "Gist 操作:\n"
    "/gh gist list\n"
    "/gh gist view <id>\n"
    "/gh gist create --files a.txt=内容 [--description 描述] [--public]\n"
    "/gh gist edit <id> --files a.txt=内容 [--description 描述]\n"
    "/gh gist comment <id> --body 内容\n"
    "/gh gist delete <id>"
)


def _item(g) -> dict:
    return {
        "id": g.id,
        "description": g.description or "",
        "html_url": g.html_url,
        "files": {name: f.content for name, f in g.files.items()},
    }


def list_gists(client, params):
    return [_item(g) for g in client.get_github().get_user().get_gists()]


def view(client, params):
    g = client.get_github().get_gist(params["id"])
    return _item(g)


def _files(raw) -> dict:
    return {name: InputFileContent(content) for name, content in raw.items()}


def create(client, params):
    raw_files = params.get("files", {})
    if not raw_files:
        raise ValueError("缺少文件内容: /gh gist create --files 文件名=内容")
    g = (
        client.get_github()
        .get_user()
        .create_gist(
            public=bool(params.get("public", False)),
            files=_files(raw_files),
            description=params.get("description") or "",
        )
    )
    return {"id": g.id, "html_url": g.html_url, "ok": True}


def delete(client, params):
    g = client.get_github().get_gist(params["id"])
    g.delete()
    return {"id": params["id"], "ok": True}


def edit(client, params):
    g = client.get_github().get_gist(params["id"])
    raw_files = params.get("files") or {}
    kwargs = {}
    if raw_files:
        kwargs["files"] = _files(raw_files)
    if params.get("description") is not None:
        kwargs["description"] = params["description"]
    if not kwargs:
        raise ValueError("缺少修改内容: /gh gist edit <id> [--files 文件名=内容] [--description 描述]")
    g.edit(**kwargs)
    return {"id": params["id"], "ok": True}


def comment(client, params):
    g = client.get_github().get_gist(params["id"])
    body = params.get("body")
    if not body:
        raise ValueError("缺少评论内容: /gh gist comment <id> --body 内容")
    c = g.create_comment(body)
    return {"id": c.id, "ok": True}


def format(data, list_limit: int, content_limit: int) -> str:
    if isinstance(data, list):
        lines = [
            f"📄 {item['id']} - {item['description'] or '（无描述）'}"
            for item in data[:list_limit]
        ]
        if len(data) > list_limit:
            lines.append(f"…已截断，共 {len(data)} 条")
        return "\n".join(lines) or "无 gist。"
    if isinstance(data, dict) and data.get("ok") is True:
        return f"✅ Gist 操作成功 {data.get('html_url', '')}"
    lines = [f"📄 {data['id']} - {data['description'] or '（无描述）'}\n"]
    for name, content in data["files"].items():
        lines.append(f"**{name}**:\n{content[:content_limit]}")
    return "\n".join(lines)


HANDLERS = {
    "list": list_gists,
    "view": view,
    "create": create,
    "edit": edit,
    "comment": comment,
    "delete": delete,
}
