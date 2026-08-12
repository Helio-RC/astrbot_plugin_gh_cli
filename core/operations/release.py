"""release group: list / view / create / delete."""

MODE = "sync"
WRITE = {"create", "edit", "delete"}

HELP = (
    "Release 操作:\n"
    "/gh release list [-R owner/repo]\n"
    "/gh release view <tag> [-R owner/repo]\n"
    "/gh release create <tag> [--name 名称] [--body 内容] [--draft] [--prerelease] [-R owner/repo]\n"
    "/gh release delete <tag> [-R owner/repo]"
)


def _repo(client, params):
    name = params.get("repo") or params.get("default_repo")
    if not name:
        raise ValueError("缺少仓库参数，请指定 -R owner/repo 或配置 default_repo。")
    return client.get_github().get_repo(name)


def _item(r) -> dict:
    return {
        "tag": r.tag_name,
        "name": r.name or r.tag_name,
        "draft": bool(r.draft),
        "prerelease": bool(r.prerelease),
        "body": (r.body or "")[:4000],
        "html_url": r.html_url,
    }


def list_releases(client, params):
    repo = _repo(client, params)
    return [_item(r) for r in repo.get_releases()]


def view(client, params):
    repo = _repo(client, params)
    return _item(repo.get_release(params["tag"]))


def create(client, params):
    repo = _repo(client, params)
    tag = params.get("tag")
    if not tag:
        raise ValueError("缺少 tag: /gh release create <tag>")
    r = repo.create_git_release(
        tag=tag,
        name=params.get("name") or tag,
        message=params.get("body") or "",
        draft=bool(params.get("draft", False)),
        prerelease=bool(params.get("prerelease", False)),
    )
    return {"tag": tag, "html_url": r.html_url, "ok": True}


def delete(client, params):
    repo = _repo(client, params)
    r = repo.get_release(params["tag"])
    r.delete_release()
    return {"tag": params["tag"], "ok": True}


def format(data, list_limit: int, content_limit: int) -> str:
    if isinstance(data, list):
        lines = []
        for item in data[:list_limit]:
            flag = "🧪" if item["prerelease"] else ("📝" if item["draft"] else "🚀")
            lines.append(f"{flag} {item['name']} ({item['tag']})")
        if len(data) > list_limit:
            lines.append(f"…已截断，共 {len(data)} 条")
        return "\n".join(lines) or "无 release。"
    if isinstance(data, dict) and data.get("ok") is True:
        return f"✅ Release 操作成功 {data.get('html_url', '')}"
    return (
        f"🚀 {data['name']} ({data['tag']})\n"
        f"{data['body'][:content_limit]}{'…' if len(data['body']) > content_limit else ''}\n"
        f"🔗 {data['html_url']}"
    )


HANDLERS = {
    "list": list_releases,
    "view": view,
    "create": create,
    "delete": delete,
}
