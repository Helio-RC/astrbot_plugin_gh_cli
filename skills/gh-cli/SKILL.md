---
name: gh-cli
description: 通过 AstrBot 插件执行 GitHub CLI 风格操作（repo/issue/pr/release/gist/search/run/api）。当用户需要查询、创建或管理 GitHub 仓库、issue、PR、release、gist，搜索 GitHub 内容，查看 Actions 运行，或调用 GitHub REST API 时使用。
---

# GitHub CLI 技能

本插件提供 8 个函数调用工具和一个 `/gh` 用户指令，底层使用 GitHub REST API。

## 工具总览

| 工具 | 用途 | 写操作（需管理员） |
|---|---|---|
| gh_repo | 仓库查看/列表/创建/编辑/加星/取消加星 | create, edit, star, unstar |
| gh_issue | issue 列表/查看/创建/关闭/重开/评论 | create, edit, close, reopen, comment, delete |
| gh_pr | PR 列表/查看/创建/合并/评论/评审 | create, edit, close, reopen, merge, comment, review, delete |
| gh_release | release 列表/查看/创建/删除 | create, edit, delete |
| gh_gist | gist 列表/查看/创建/删除 | create, edit, delete, comment |
| gh_search | 搜索仓库/issue/PR/用户/代码 | 无 |
| gh_run | Actions 运行列表/详情/触发 | run |
| gh_api | 原始 REST API | POST/PATCH/PUT/DELETE |

## 调用约定

1. 每个工具第一个参数 `action` 必填，取值见各工具 schema 的 enum。
2. 每次调用必须传入 `sender_name`（发起操作的调用者名字）和 `umo`（当前会话标识 unified_msg_origin），用于审计记录；从对话上下文中获取。
3. 仓库参数：优先传 `repo`（owner/repo）；未传时使用插件配置的 `default_repo`。
4. 写操作（创建/合并/删除/评论/关闭/触发等）仅在插件开启对应写开关且调用者是管理员时可用；被拒绝时工具返回明确提示。若开启了 `bot_write`，AI 工具调用时机器人自身视为管理员，不再要求发起者管理员；若未开启，写操作还要求发起者是管理员。
5. 列表类操作默认返回 10 条；长正文会被截断。
6. 若配置了 `text_prefix`（长文本自动前缀），创建/评论类操作传入的 `body` 会自动加上前缀段落（如"本消息由机器人发送"）。不要在 `body` 里重复撰写该说明，只需提供实际内容。

## 典型用法

- 查仓库: `gh_repo(action="view", repo="octocat/Hello-World")`
- 列 issue: `gh_issue(action="list", repo="o/r", state="open")`
- 建 issue: `gh_issue(action="create", repo="o/r", title="标题", body="内容")`（写操作）
- 看 PR: `gh_pr(action="view", repo="o/r", number=42)`
- 搜仓库: `gh_search(action="repos", query="astrbot")`
- 看 Actions: `gh_run(action="runs", repo="o/r")`
- 原生 API: `gh_api(action="call", path="/repos/o/r", method="GET")`

## 用户指令（供向用户解释）

用户也可直接输入 `/gh <指令组> <操作>` 使用，例如 `/gh issue list -R octocat/Hello-World`。详细帮助：`/gh help`。

## 注意事项

- 不要尝试读取或展示任何 Token。
- 删除/合并等破坏性操作必须先向用户确认再调用。
- API 返回错误时，将错误消息原样反馈给用户。
- 所有操作都会被审计记录（时间、发起人、操作、结果），可在插件 WebUI 的"审计日志"页面查看。
