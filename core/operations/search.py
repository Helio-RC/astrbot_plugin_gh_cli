"""search group: repos / issues / prs / users / commits / code."""

MODE = "sync"
WRITE = set()

HELP = (
    "搜索:\n"
    "/gh search repos <关键词>\n"
    "/gh search issues <关键词> [--repo owner/repo]\n"
    "/gh search prs <关键词> [--repo owner/repo]\n"
    "/gh search users <关键词>\n"
    "/gh search code <关键词> [--repo owner/repo]"
)


def repos(client, params):
    q = params.get("query")
    if not q:
        raise ValueError("缺少搜索词: /gh search repos <关键词>")
    return [
        {
            "full_name": r.full_name,
            "description": getattr(r, "description", None) or "",
            "stargazers_count": r.stargazers_count,
            "language": getattr(r, "language", "") or "",
        }
        for r in client.get_github().search_repositories(q)
    ]


def issues(client, params):
    return _search_issues(client, params, is_pr=False)


def prs(client, params):
    return _search_issues(client, params, is_pr=True)


def _search_issues(client, params, is_pr):
    q = params.get("query")
    if not q:
        raise ValueError("缺少搜索词")
    if params.get("repo"):
        q += f" repo:{params['repo']}"
    if is_pr:
        q += " is:pr"
    else:
        q += " is:issue"
    return [
        {
            "number": i.number,
            "title": i.title,
            "state": i.state,
            "html_url": i.html_url,
        }
        for i in client.get_github().search_issues(q)
    ]


def users(client, params):
    q = params.get("query")
    if not q:
        raise ValueError("缺少搜索词")
    return [
        {"login": u.login, "html_url": u.html_url}
        for u in client.get_github().search_users(q)
    ]


def code(client, params):
    q = params.get("query")
    if not q:
        raise ValueError("缺少搜索词")
    if params.get("repo"):
        q += f" repo:{params['repo']}"
    return [
        {
            "path": c.path,
            "repository": c.repository.full_name,
            "html_url": c.html_url,
        }
        for c in client.get_github().search_code(q)
    ]


def format(data, list_limit: int, content_limit: int) -> str:
    if not isinstance(data, list):
        return str(data)
    lines = []
    for item in data[:list_limit]:
        if "full_name" in item:
            desc = item["description"][:content_limit] if item["description"] else ""
            lines.append(
                f"⭐{item['stargazers_count']} {item['full_name']}{' - ' + desc if desc else ''}"
            )
        elif "login" in item:
            lines.append(f"👤 {item['login']}")
        elif "path" in item:
            lines.append(f"📄 {item['repository']} {item['path']}")
        else:
            lines.append(f"#{item['number']} {item['title']} ({item['state']})")
    if len(data) > list_limit:
        lines.append(f"…已截断，共 {len(data)} 条")
    return "\n".join(lines) or "无结果。"


HANDLERS = {
    "repos": repos,
    "issues": issues,
    "prs": prs,
    "users": users,
    "code": code,
}
