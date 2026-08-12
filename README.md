# astrbot_plugin_gh_cli

GitHub CLI 插件：在 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 聊天中直接使用 GitHub CLI 风格的指令与 AI 函数调用，管理仓库、Issue、PR、Release、Gist、Actions，执行搜索与原始 REST API 请求。

插件名称：`astrbot_plugin_gh_cli`，版本：v1.0.0

## 功能特性

- **8 个指令组**：`repo`（仓库）、`issue`（问题）、`pr`（拉取请求）、`release`（发布）、`gist`（代码片段）、`search`（搜索）、`run`（Actions 运行）、`api`（原始 REST API）。
- **`/gh` 用户指令**：命令行风格语法，如 `/gh issue list -R octocat/Hello-World`，输入 `/gh help` 查看完整帮助。
- **AI 函数调用**：注册 8 个 LLM 工具（`gh_repo` / `gh_issue` / `gh_pr` / `gh_release` / `gh_gist` / `gh_search` / `gh_run` / `gh_api`），供 AstrBot 的 AI Agent 调用。
- **技能文件**：内置 `skills/gh-cli/SKILL.md`，指导 AI 正确使用这些工具。
- **功能开关**：每个指令组可独立启用/禁用；写操作（创建/编辑/合并/删除/评论/触发等）需管理员权限且需在配置中单独开启。
- **加密凭据库**：Token 经 Fernet 加密后落盘（`secrets.json` 0600），配置文件中不留明文；支持共享 Token 与多份个人 Token，用户可通过 `/gh auth use <名称>` 切换身份。
- **权限控制**：普通用户只能执行只读操作；写操作与原始 API 写请求默认关闭，需管理员开启并仅限管理员执行。

## 安装

将本插件克隆到 AstrBot 的插件目录：

```bash
cd <AstrBot 数据目录>/data/plugins
git clone <本插件仓库地址> astrbot_plugin_gh_cli
```

> **注意**：目录名必须是合法的 Python 标识符（如 `astrbot_plugin_gh_cli`），因为插件会作为 Python 模块被导入。请勿使用带连字符或空格的目录名（如 `astrbot-plugin-gh-cli`）。

安装依赖（如未自动安装）：

```bash
pip install -r requirements.txt
```

在 AstrBot 管理后台启用插件并重启 AstrBot。

## 配置说明

在 AstrBot 管理后台打开插件配置，按需填写：

| 配置项 | 说明 |
|---|---|
| `shared_token` | 共享 GitHub Token。保存后会被自动加密移入凭据库，配置文件中不再留明文。 |
| `personal_tokens` | 个人 Token 列表（名称 + Token）。用户可在聊天中用 `/gh auth use <名称>` 切换身份。 |
| `default_repo` | 默认仓库 `owner/repo`，未带 `-R` 参数时使用。 |
| `enable_repo` / `repo_write` | 仓库组开关 / 是否允许仓库写操作（`create/edit/star/unstar`）。 |
| `enable_issue` / `issue_write` | Issue 组开关 / 是否允许写操作（`create/edit/close/reopen/comment/delete`）。 |
| `enable_pr` / `pr_write` | PR 组开关 / 是否允许写操作（`create/edit/close/reopen/merge/comment/review/delete`）。 |
| `enable_release` / `release_write` | Release 组开关 / 是否允许写操作（`create/edit/delete`）。 |
| `enable_gist` / `gist_write` | Gist 组开关 / 是否允许写操作（`create/edit/delete/comment`）。 |
| `enable_search` / `search_write` | 搜索组开关（无写操作）。 |
| `enable_run` / `run_write` | Actions 组开关 / 是否允许触发工作流（`run`）。 |
| `enable_api` / `api_write` | 原始 API 组开关 / 是否允许写请求（`POST/PATCH/PUT/DELETE`）。 |
| `list_limit` | 列表默认返回条数（1-30）。 |
| `content_limit` | 长正文截断字符数。 |

写操作即使开关打开，也只有**管理员**（`is_admin`）能够执行。

## `/gh` 使用示例

```
/gh help                                  # 查看完整帮助
/gh auth status                           # 查看当前身份
/gh auth use alice                        # 切换到个人 Token「alice」

/gh repo view -R octocat/Hello-World      # 查看仓库
/gh repo list                             # 列出我的仓库
/gh issue list -R octocat/Hello-World --state open
/gh issue create --title 标题 --body 内容 -R octocat/Hello-World
/gh pr view 42 -R octocat/Hello-World
/gh release list -R octocat/Hello-World
/gh gist create --files a.txt=内容 --public
/gh search repos astrbot
/gh run list -R octocat/Hello-World
/gh api /repos/octocat/Hello-World        # GET
/gh api /repos/octocat/Hello-World/issues --method POST --body '{"title":"hi"}'
```

通用参数：`-R owner/repo` 指定仓库（缺省用配置的 `default_repo`）；布尔开关如 `--private`、`--draft`、`--prerelease`。

## 加密凭据与环境变量

插件用 Fernet 对称加密存储所有 Token（写入 `<数据目录>/plugin_data/astrbot_plugin_gh_cli/data/secrets.json`，文件权限 0600）。

主密钥来源：

1. 优先读取环境变量 `ASTRBOT_GH_MASTER_KEY`（需为 Fernet 格式的 32 字节 URL-safe base64 密钥，可用 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` 生成）。
2. 若未设置，则自动生成随机主密钥并持久化到 `master.key`（0600），并输出一条警告日志。

> 若设置了 `ASTRBOT_GH_MASTER_KEY`，请务必妥善保管并在每次启动时提供一致的密钥，否则已加密的 `secrets.json` 无法解密。若使用自动生成的 `master.key`，请保留该文件，重启后可正常解密。

## AI 函数调用

启用后，AstrBot 的 AI Agent 会自动获得 8 个 GitHub 工具（`gh_repo`、`gh_issue`、`gh_pr`、`gh_release`、`gh_gist`、`gh_search`、`gh_run`、`gh_api`）。每个工具的首参 `action` 为必填，写操作同样受对应开关约束（若开启 `bot_write`，AI 工具调用时机器人自身视为管理员，无需发起者管理员；`/gh` 指令仍要求用户管理员）。技能说明见 `skills/gh-cli/SKILL.md`。

## 开发与测试

安装开发依赖并运行测试：

```bash
pip install -r requirements.txt pytest pytest-asyncio ruff
ruff check .
ruff format .
pytest tests -v
```

要求：`ruff check` 无错误、`ruff format` 无改动、全部测试通过且输出无警告。
