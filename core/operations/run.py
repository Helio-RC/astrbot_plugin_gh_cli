"""run group: GitHub Actions runs via raw REST (async)."""

from urllib.parse import quote

MODE = "async"
WRITE = {"run"}

HELP = (
    "Actions 运行:\n"
    "/gh run list [-R owner/repo] [--workflow 名称]\n"
    "/gh run runs [-R owner/repo] [--workflow 名称]\n"
    "/gh run view <run_id> [-R owner/repo]\n"
    "/gh run run --workflow 名称 [--ref main] [-R owner/repo]"
)


def _base(params):
    repo = params.get("repo") or params.get("default_repo")
    if not repo:
        raise ValueError("缺少仓库参数，请指定 -R owner/repo 或配置 default_repo。")
    return f"/repos/{repo}/actions"


async def list_workflows(client, params):
    status, data = await client.rest("GET", f"{_base(params)}/workflows")
    if status != 200:
        raise ValueError(f"获取工作流失败 (HTTP {status})")
    return [
        {"name": w["name"], "state": w["state"], "path": w["path"]}
        for w in data.get("workflows", [])
    ]


async def runs(client, params):
    base = _base(params)
    qp = {"per_page": params.get("limit", 10)}
    if params.get("workflow"):
        qp["workflow"] = quote(params["workflow"], safe="")
    status, data = await client.rest("GET", f"{base}/runs", params=qp)
    if status != 200:
        raise ValueError(f"获取运行列表失败 (HTTP {status})")
    return {
        "total": data.get("total_count", 0),
        "runs": [
            {
                "id": r["id"],
                "name": r.get("name") or r.get("display_title", ""),
                "status": r["status"],
                "conclusion": r.get("conclusion") or "",
                "branch": r.get("head_branch", ""),
                "number": r.get("run_number"),
                "html_url": r["html_url"],
            }
            for r in data.get("workflow_runs", [])
        ],
    }


async def view(client, params):
    status, data = await client.rest(
        "GET", f"{_base(params)}/runs/{int(params['run_id'])}"
    )
    if status != 200:
        raise ValueError(f"获取运行详情失败 (HTTP {status})")
    return {
        "id": data["id"],
        "name": data.get("name") or data.get("display_title", ""),
        "status": data["status"],
        "conclusion": data.get("conclusion") or "",
        "branch": data.get("head_branch", ""),
        "created_at": data.get("created_at", ""),
        "html_url": data["html_url"],
    }


async def dispatch(client, params):
    workflow = params.get("workflow")
    if not workflow:
        raise ValueError("缺少工作流: /gh run run --workflow 名称")
    status, data = await client.rest(
        "POST",
        f"{_base(params)}/workflows/{quote(workflow, safe='')}/dispatches",
        body={"ref": params.get("ref", "main")},
    )
    if status not in (201, 204):
        raise ValueError(f"触发工作流失败 (HTTP {status}): {data}")
    return {"ok": True, "workflow": workflow, "ref": params.get("ref", "main")}


def format(data, list_limit: int, content_limit: int) -> str:
    if isinstance(data, dict) and "runs" in data:
        lines = []
        for r in data["runs"][:list_limit]:
            state = (
                "✅"
                if r["conclusion"] == "success"
                else ("❌" if r["conclusion"] else "⏳")
            )
            lines.append(
                f"{state} {r['number']} {r['name']} ({r['status']}/{r['conclusion']})"
            )
        if len(data["runs"]) > list_limit:
            lines.append(f"…已截断，共 {data['total']} 条")
        return "\n".join(lines) or "无运行记录。"
    if isinstance(data, list):
        return (
            "\n".join(f"📄 {w['name']} ({w['state']})" for w in data[:list_limit])
            or "无工作流。"
        )
    if isinstance(data, dict) and data.get("ok") is True:
        return f"✅ 已触发工作流 {data['workflow']} @ {data['ref']}"
    return f"▶️ {data['name']} ({data['status']}/{data['conclusion']})\n🔗 {data['html_url']}"


HANDLERS = {
    "list": list_workflows,
    "runs": runs,
    "view": view,
    "run": dispatch,
}
