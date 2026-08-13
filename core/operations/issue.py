"""issue group: list / view / create / edit / close / reopen / comment."""

MODE = "sync"
WRITE = {"create", "edit", "close", "reopen", "comment"}

HELP = (
    "Issue 操作:\n"
    "/gh issue list [-R owner/repo] [--state open|closed|all]\n"
    "/gh issue view <number> [-R owner/repo]\n"
    "/gh issue create --title 标题 [--body 内容] [-R owner/repo] [--labels a,b]\n"
    "/gh issue edit <number> [--labels a,b] [--title 标题] [--body 内容] [-R owner/repo]\n"
    "/gh issue close <number> [-R owner/repo]\n"
    "/gh issue comment <number> --body 内容 [-R owner/repo]"
)


def _repo(client, params):
    name = params.get("repo") or params.get("default_repo")
    if not name:
        raise ValueError("缺少仓库参数，请指定 -R owner/repo 或配置 default_repo。")
    return client.get_github().get_repo(name)


def _item(i) -> dict:
    return {
        "number": i.number,
        "title": i.title,
        "state": i.state,
        "labels": [l.name for l in getattr(i, "labels", [])],
        "user": getattr(getattr(i, "user", None), "login", ""),
        "html_url": i.html_url,
        "body": (i.body or "")[:4000],
    }


def list_issues(client, params):
    repo = _repo(client, params)
    state = params.get("state", "open")
    items = [
        i for i in repo.get_issues(state=state) if not getattr(i, "pull_request", None)
    ]
    return [_item(i) for i in items]


def view(client, params):
    repo = _repo(client, params)
    return _item(repo.get_issue(int(params["number"])))


def _labels(raw) -> list[str]:
    return [l.strip() for l in raw.split(",") if l.strip()]


def create(client, params):
    repo = _repo(client, params)
    title = params.get("title")
    if not title:
        raise ValueError("缺少标题: /gh issue create --title 标题")
    labels = _labels(params.get("labels") or "")
    i = repo.create_issue(title=title, body=params.get("body") or "", labels=labels)
    return {"number": i.number, "html_url": i.html_url, "ok": True}


def edit(client, params):
    repo = _repo(client, params)
    i = repo.get_issue(int(params["number"]))
    kwargs = {}
    if params.get("labels") is not None:
        kwargs["labels"] = _labels(params["labels"])
    if params.get("title"):
        kwargs["title"] = params["title"]
    if params.get("body") is not None:
        kwargs["body"] = params["body"]
    if params.get("state"):
        kwargs["state"] = params["state"]
    if not kwargs:
        raise ValueError("缺少修改内容: /gh issue edit <n> [--labels a,b] [--title 标题] [--body 内容]")
    i.edit(**kwargs)
    return {"number": i.number, "html_url": i.html_url, "ok": True}


def close(client, params):
    repo = _repo(client, params)
    i = repo.get_issue(int(params["number"]))
    i.edit(state="closed")
    return {"number": i.number, "state": "closed", "ok": True}


def reopen(client, params):
    repo = _repo(client, params)
    i = repo.get_issue(int(params["number"]))
    i.edit(state="open")
    return {"number": i.number, "state": "open", "ok": True}


def comment(client, params):
    repo = _repo(client, params)
    body = params.get("body")
    if not body:
        raise ValueError("缺少评论内容: /gh issue comment <n> --body 内容")
    c = repo.get_issue(int(params["number"])).create_comment(body)
    return {"id": c.id, "ok": True}


def format(data, list_limit: int, content_limit: int) -> str:
    if isinstance(data, list):
        lines = []
        for item in data[:list_limit]:
            mark = "✅" if item["state"] == "closed" else "🟢"
            labels = " ".join(f"#{l}" for l in item.get("labels", []))
            lines.append(f"{mark} #{item['number']} {item['title']} {labels}")
        if len(data) > list_limit:
            lines.append(f"…已截断，共 {len(data)} 条")
        return "\n".join(lines) or "无 issue。"
    if isinstance(data, dict) and data.get("ok") is True:
        num = f"#{data['number']}" if "number" in data else ""
        return f"✅ Issue 操作成功 ({num}) {data.get('html_url', '')}"
    return (
        f"#{data['number']} {data['title']} ({data['state']})\n"
        f"👤 {data['user']} 🏷️ {', '.join('#' + l for l in data['labels']) or '无'}\n"
        f"{data['body'][:content_limit]}{'…' if len(data['body']) > content_limit else ''}\n"
        f"🔗 {data['html_url']}"
    )


HANDLERS = {
    "list": list_issues,
    "view": view,
    "create": create,
    "edit": edit,
    "close": close,
    "reopen": reopen,
    "comment": comment,
}
