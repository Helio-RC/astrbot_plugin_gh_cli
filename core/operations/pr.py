"""pr group: list / view / create / edit / close / reopen / merge / comment / review."""

MODE = "sync"
WRITE = {"create", "edit", "close", "reopen", "merge", "comment", "review"}

HELP = (
    "PR 操作:\n"
    "/gh pr list [-R owner/repo] [--state open|closed|merged|all]\n"
    "/gh pr view <number> [-R owner/repo]\n"
    "/gh pr create --title 标题 --head 分支 [--base main] [--body 内容] [-R owner/repo]\n"
    "/gh pr edit <number> [--title 标题] [--body 内容] [--labels a,b] [-R owner/repo]\n"
    "/gh pr merge <number> [-R owner/repo] [--method merge|squash|rebase]\n"
    "/gh pr close <number> | /gh pr reopen <number>\n"
    "/gh pr comment <number> --body 内容\n"
    "/gh pr review <number> --event approve|request_changes|comment [--body 内容]"
)


def _repo(client, params):
    name = params.get("repo") or params.get("default_repo")
    if not name:
        raise ValueError("缺少仓库参数，请指定 -R owner/repo 或配置 default_repo。")
    return client.get_github().get_repo(name)


def _item(p) -> dict:
    return {
        "number": p.number,
        "title": p.title,
        "state": p.state,
        "head": getattr(getattr(p, "head", None), "ref", ""),
        "base": getattr(getattr(p, "base", None), "ref", ""),
        "merged": bool(getattr(p, "merged", False)),
        "user": getattr(getattr(p, "user", None), "login", ""),
        "html_url": p.html_url,
        "body": (getattr(p, "body", None) or "")[:4000],
    }


def list_prs(client, params):
    repo = _repo(client, params)
    state = params.get("state", "open")
    return [_item(p) for p in repo.get_pulls(state=state)]


def view(client, params):
    repo = _repo(client, params)
    return _item(repo.get_pull(int(params["number"])))


def create(client, params):
    repo = _repo(client, params)
    title = params.get("title")
    head = params.get("head")
    if not title or not head:
        raise ValueError("缺少参数: /gh pr create --title 标题 --head 分支")
    p = repo.create_pull(
        title=title,
        body=params.get("body") or "",
        head=head,
        base=params.get("base", "main"),
    )
    return {"number": p.number, "html_url": p.html_url, "ok": True}


def close(client, params):
    repo = _repo(client, params)
    p = repo.get_pull(int(params["number"]))
    p.edit(state="closed")
    return {"number": p.number, "ok": True}


def edit(client, params):
    repo = _repo(client, params)
    p = repo.get_pull(int(params["number"]))
    kwargs = {}
    if params.get("title"):
        kwargs["title"] = params["title"]
    if params.get("body") is not None:
        kwargs["body"] = params["body"]
    if params.get("labels") is not None:
        kwargs["labels"] = [
            l.strip() for l in params["labels"].split(",") if l.strip()
        ]
    if params.get("state"):
        kwargs["state"] = params["state"]
    if params.get("base"):
        kwargs["base"] = params["base"]
    if not kwargs:
        raise ValueError("缺少修改内容: /gh pr edit <n> [--title 标题] [--body 内容] [--labels a,b]")
    p.edit(**kwargs)
    return {"number": p.number, "ok": True}


def reopen(client, params):
    repo = _repo(client, params)
    p = repo.get_pull(int(params["number"]))
    p.edit(state="open")
    return {"number": p.number, "ok": True}


def merge(client, params):
    repo = _repo(client, params)
    p = repo.get_pull(int(params["number"]))
    method = params.get("method")
    p.merge(merge_method=method) if method else p.merge()
    return {"number": p.number, "merged": True, "ok": True}


def comment(client, params):
    repo = _repo(client, params)
    body = params.get("body")
    if not body:
        raise ValueError("缺少评论内容: /gh pr comment <n> --body 内容")
    c = repo.get_pull(int(params["number"])).create_issue_comment(body)
    return {"id": c.id, "ok": True}


def review(client, params):
    repo = _repo(client, params)
    event = params.get("event", "comment").upper()
    if event == "REQUEST_CHANGES":
        event = "REQUEST_CHANGES"
    body = params.get("body") or ""
    repo.get_pull(int(params["number"])).create_review(
        event=event, body=body if body else None
    )
    return {"number": int(params["number"]), "ok": True}


def format(data, list_limit: int, content_limit: int) -> str:
    if isinstance(data, list):
        lines = []
        for item in data[:list_limit]:
            state = {
                "open": "🟢",
                "closed": "🔒",
                "merged": "✅",
            }.get(item["state"], "⚪")
            lines.append(
                f"{state} #{item['number']} {item['title']} "
                f"({item.get('head', '')} → {item.get('base', '')})"
            )
        if len(data) > list_limit:
            lines.append(f"…已截断，共 {len(data)} 条")
        return "\n".join(lines) or "无 PR。"
    if isinstance(data, dict) and data.get("ok") is True:
        return f"✅ PR 操作成功 #{data.get('number', '')} {data.get('html_url', '')}"
    return (
        f"PR #{data['number']} {data['title']} ({data['state']})\n"
        f"👤 {data['user']} {data['head']} → {data['base']}\n"
        f"{data['body'][:content_limit]}{'…' if len(data['body']) > content_limit else ''}\n"
        f"🔗 {data['html_url']}"
    )


HANDLERS = {
    "list": list_prs,
    "view": view,
    "create": create,
    "edit": edit,
    "close": close,
    "reopen": reopen,
    "merge": merge,
    "comment": comment,
    "review": review,
}
