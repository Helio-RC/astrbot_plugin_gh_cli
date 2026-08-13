# Changelog

## [v1.0.1]

### 新增

- `issue edit`：支持给已有 issue 打标签（`--labels a,b`）及修改标题/正文/状态。LLM 现可通过 `gh_issue(action="edit", number=…, labels="…")` 给 issue 打 tag（此前该操作不存在，LLM 只能靠 `gh_api` 绕行）。
- `pr edit`：支持修改 PR 标题/正文/标签/状态/base 分支。
- `release edit`：支持修改 release 名称/说明/draft/prerelease。
- `gist edit` / `gist comment`：支持编辑 gist 文件与描述、发表评论。
- 以上操作自动进入对应 LLM 工具的 `action` enum，写操作开关/管理员校验与既有模型一致。

### 修复

- **api 组写权限门失效（安全）**：`gh_api` 的 action 恒为 `call`，不在 `WRITE`（HTTP 方法集合）内，导致 `POST/PATCH/PUT/DELETE` 写请求从未经过权限校验，任何非管理员都能直接调用。现通过模块级 `write_key()` 钩子将权限键映射为 HTTP method：GET 任意用户放行，写方法仍需 `api_write` 开关 + 管理员（或 `bot_write`）。
- 移除 `issue`/`pr` 组中声明但无法实现的 `delete`（GitHub REST API 不支持删除 issue/PR），`WRITE` 集合与文档同步对齐。

### 变更

- `issue`/`pr` 的 `edit` 操作加入 `LONG_TEXT_ACTIONS`，配置 `text_prefix` 时 `--body` 会自动加前缀。
- `README.md`、`skills/gh-cli/SKILL.md` 写操作列表与实现对齐。

### 测试

- 新增 issue/pr/release/gist 各 edit（及 gist comment）handler 用例；新增 api 权限门用例（GET 放行、写方法需开关+管理员）；断言 `gh_issue` action enum 含 `edit`。

## [v1.0.0]

- 初始版本：8 组 GitHub 操作（repo/issue/pr/release/gist/search/run/api），`/gh` 指令与 LLM 函数调用双入口。
- 功能开关（每组独立 `enable_*` / `*_write`）、`bot_write`、`text_prefix` 等配置项。
- 共享/个人 Token 加密存储（Vault）、`/gh auth use|status` 身份切换。
- 操作审计日志（WebUI 列表/清空/导出/统计）。
- `default_repo` 实时读取、支持粘贴仓库链接自动归一化；`/gh` 前缀兼容。
