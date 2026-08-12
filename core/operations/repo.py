"""repo group: view / list / create / edit / star / unstar."""

from ..client import GhClient

MODE = "sync"
WRITE = {"create", "edit", "star", "unstar"}

HELP = (
    "仓库操作:\n"
    "/gh repo view [-R owner/repo]\n"
    "/gh repo list [--user owner]\n"
    "/gh repo create <name> [--private] [--description 描述]\n"
    "/gh repo star <owner/repo> | /gh repo unstar <owner/repo>"
)


def _repo_or_default(client: GhClient, params: dict):
    name = params.get("repo")
    return name if name else params.get("default_repo")


def view(client, params):
    name = _repo_or_default(client, params)
    if not name:
        raise ValueError("缺少仓库参数，请指定 -R owner/repo 或配置 default_repo。")
    r = client.get_github().get_repo(name)
    return {
        "full_name": r.full_name,
        "description": r.description or "",
        "html_url": r.html_url,
        "stargazers_count": r.stargazers_count,
        "forks_count": r.forks_count,
        "open_issues_count": r.open_issues_count,
        "language": r.language or "",
        "default_branch": r.default_branch,
        "private": r.private,
        "created_at": str(getattr(r, "created_at", "")),
        "updated_at": str(getattr(r, "updated_at", "")),
    }


def list_repos(client, params):
    g = client.get_github()
    user = params.get("user")
    if user:
        repos = g.get_user(user).get_repos()
    else:
        repos = g.get_user().get_repos()
    return [
        {
            "full_name": r.full_name,
            "description": r.description or "",
            "stargazers_count": r.stargazers_count,
            "language": r.language or "",
            "private": r.private,
        }
        for r in repos
    ]


def create(client, params):
    name = params.get("name")
    if not name:
        raise ValueError("缺少仓库名: /gh repo create <name>")
    g = client.get_github()
    r = g.get_user().create_repo(
        name,
        description=params.get("description") or "",
        private=bool(params.get("private", False)),
    )
    return {"full_name": r.full_name, "html_url": r.html_url}


def edit(client, params):
    name = _repo_or_default(client, params)
    if not name:
        raise ValueError("缺少仓库参数，请指定 -R owner/repo。")
    kwargs = {}
    if params.get("description") is not None:
        kwargs["description"] = params["description"]
    r = client.get_github().get_repo(name)
    r.edit(**kwargs)
    return {"full_name": r.full_name, "ok": True}


def star(client, params):
    name = _repo_or_default(client, params)
    if not name:
        raise ValueError("缺少仓库参数。")
    client.get_github().get_user().add_to_starred(client.get_github().get_repo(name))
    return {"ok": True, "starred": name}


def unstar(client, params):
    name = _repo_or_default(client, params)
    if not name:
        raise ValueError("缺少仓库参数。")
    client.get_github().get_user().remove_from_starred(
        client.get_github().get_repo(name)
    )
    return {"ok": True, "unstarred": name}


def format(data, list_limit: int, content_limit: int) -> str:
    if isinstance(data, list):
        lines = []
        for item in data[:list_limit]:
            lines.append(
                f"⭐{item['stargazers_count']} {item['full_name']}"
                + (
                    f" - {item['description'][:content_limit]}"
                    if item["description"]
                    else ""
                )
            )
        if len(data) > list_limit:
            lines.append(f"…已截断，共 {len(data)} 条")
        return "\n".join(lines) or "无仓库。"
    if isinstance(data, dict) and data.get("ok") is True:
        if "starred" in data:
            return f"✅ 已加星 {data['starred']}。"
        if "unstarred" in data:
            return f"✅ 已取消加星 {data['unstarred']}。"
        return f"✅ 仓库 {data.get('full_name', '')} 操作成功。"
    return (
        f"📦 {data['full_name']}\n"
        f"{data.get('description') or '（无描述）'}\n"
        f"⭐{data['stargazers_count']} 🍴{data['forks_count']} "
        f"🐞{data['open_issues_count']} {data.get('language', '')}\n"
        f"分支: {data['default_branch']} 私有: {'是' if data['private'] else '否'}\n"
        f"🔗 {data['html_url']}"
    )


HANDLERS = {
    "view": view,
    "list": list_repos,
    "create": create,
    "edit": edit,
    "star": star,
    "unstar": unstar,
}
