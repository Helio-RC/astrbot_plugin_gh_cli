"""Pure-data LLM tool schemas (JSON Schema), shared by tests and tools.py."""

from .operations import registry


def _action_enums(group: str) -> list[str]:
    return sorted(registry.get_group(group).HANDLERS)


def _schema(name: str, desc: str, group: str, extra: dict) -> dict:
    return {
        "name": name,
        "description": desc,
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": _action_enums(group),
                    "description": f"要执行的操作。写操作: {sorted(registry.get_group(group).WRITE)}",
                },
                "sender_name": {
                    "type": "string",
                    "description": "发起本次操作的调用者名字（必须传入，用于审计记录）",
                },
                "umo": {
                    "type": "string",
                    "description": "发起本次操作的会话标识 unified_msg_origin（必须传入，用于审计记录）",
                },
                **extra,
            },
            "required": ["action"],
        },
    }


STR = lambda desc, enum=None: (
    {"type": "string", "enum": enum, "description": desc}
    if enum
    else {"type": "string", "description": desc}
)


def _build() -> dict:
    schemas = {}
    schemas["gh_repo"] = _schema(
        "gh_repo",
        "GitHub 仓库操作（查看/列表/创建/编辑/加星）",
        "repo",
        {
            "repo": STR("仓库名 owner/repo；缺省用 default_repo"),
            "name": STR("创建仓库时的仓库名"),
            "description": STR("描述"),
            "private": {"type": "boolean", "description": "是否私有仓库"},
            "user": STR("仓库所有者（list 时）"),
        },
    )
    schemas["gh_issue"] = _schema(
        "gh_issue",
        "GitHub Issue 操作（列表/查看/创建/关闭/重开/评论）",
        "issue",
        {
            "repo": STR("仓库名 owner/repo；缺省用 default_repo"),
            "number": STR("issue 编号"),
            "title": STR("标题"),
            "body": STR("内容"),
            "state": STR("状态", ["open", "closed", "all"]),
            "labels": STR("标签，逗号分隔"),
        },
    )
    schemas["gh_pr"] = _schema(
        "gh_pr",
        "GitHub PR 操作（列表/查看/创建/合并/评论/评审）",
        "pr",
        {
            "repo": STR("仓库名 owner/repo；缺省用 default_repo"),
            "number": STR("PR 编号"),
            "title": STR("标题"),
            "body": STR("内容"),
            "head": STR("源分支"),
            "base": STR("目标分支，默认 main"),
            "state": STR("状态", ["open", "closed", "merged", "all"]),
            "method": STR("合并方式", ["merge", "squash", "rebase"]),
            "event": STR("评审结论", ["approve", "request_changes", "comment"]),
        },
    )
    schemas["gh_release"] = _schema(
        "gh_release",
        "GitHub Release 操作（列表/查看/创建/删除）",
        "release",
        {
            "repo": STR("仓库名 owner/repo；缺省用 default_repo"),
            "tag": STR("标签名"),
            "name": STR("Release 名称"),
            "body": STR("内容"),
            "draft": {"type": "boolean", "description": "草稿"},
            "prerelease": {"type": "boolean", "description": "预发布"},
        },
    )
    schemas["gh_gist"] = _schema(
        "gh_gist",
        "GitHub Gist 操作（列表/查看/创建/删除）",
        "gist",
        {
            "id": STR("gist id"),
            "description": STR("描述"),
            "files": {
                "type": "object",
                "description": '文件名到内容的映射，如 {"a.txt": "hello"}',
                "additionalProperties": {"type": "string"},
            },
            "public": {"type": "boolean", "description": "是否公开"},
        },
    )
    schemas["gh_search"] = _schema(
        "gh_search",
        "GitHub 搜索（仓库/issue/PR/用户/代码）",
        "search",
        {
            "action": {
                "type": "string",
                "enum": ["repos", "issues", "prs", "users", "code"],
                "description": "搜索类型（无写操作）",
            },
            "query": STR("搜索关键词"),
            "repo": STR("限定仓库 owner/repo"),
        },
    )
    schemas["gh_run"] = _schema(
        "gh_run",
        "GitHub Actions 运行查看与触发（写操作: run）",
        "run",
        {
            "repo": STR("仓库名 owner/repo；缺省用 default_repo"),
            "workflow": STR("工作流名称"),
            "run_id": STR("运行 ID"),
            "ref": STR("触发分支，默认 main"),
            "limit": {"type": "number", "description": "返回条数"},
        },
    )
    schemas["gh_api"] = _schema(
        "gh_api",
        "GitHub 原始 REST API（GET 默认；写请求需管理员）",
        "api",
        {
            "method": STR("HTTP 方法", ["GET", "POST", "PATCH", "PUT", "DELETE"]),
            "path": STR("API 路径，如 /repos/octocat/Hello-World"),
            "body": STR("请求体 JSON 字符串"),
            "query": {
                "type": "object",
                "description": "查询参数",
                "additionalProperties": {"type": "string"},
            },
        },
    )
    return schemas


TOOL_SCHEMAS = _build()
