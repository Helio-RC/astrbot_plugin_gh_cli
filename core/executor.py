"""Permission gate, dispatch, and unified error handling."""

import logging
from datetime import datetime

from github import GithubException, RateLimitExceededException

from .audit import AuditLog
from .client import AuthError, GhClient, GhError
from .config_ingest import normalize_default_repo
from .operations import registry
from .text_prefix import apply_prefix
from .vault import Vault

logger = logging.getLogger(__name__)

# (group, action) pairs whose long-text "body" parameter gets the configured
# text_prefix prepended. Short description fields are deliberately excluded.
LONG_TEXT_ACTIONS = {
    "issue": {"create", "edit", "comment"},
    "pr": {"create", "edit", "comment", "review"},
    "release": {"create"},
}


class Executor:
    def __init__(
        self,
        config_getter,
        vault: Vault,
        audit: AuditLog | None = None,
    ) -> None:
        """`config_getter` is a zero-arg callable returning the live plugin
        config, so dashboard config changes take effect without a reload."""
        self._config_getter = config_getter
        self.vault = vault
        self.audit = audit

    @property
    def config(self) -> dict:
        return self._config_getter()

    def _group_enabled(self, group: str) -> bool:
        return bool(self.config.get(f"enable_{group}", True))

    def _write_enabled(self, group: str) -> bool:
        return bool(self.config.get(f"{group}_write", False))

    def check_permission(
        self, group: str, action: str, is_admin: bool, params: dict | None = None
    ) -> str | None:
        try:
            mod = registry.get_group(group)
        except KeyError:
            return f"不支持的指令组: {group}。输入 /gh help 查看可用功能。"
        if not self._group_enabled(group):
            return f"指令组 {group} 未启用，请管理员在插件配置中打开开关。"
        # 部分指令组（如 api）的 action 与实际写操作键不一致，由模块提供 write_key 映射
        write_key = getattr(mod, "write_key", None)
        candidate = write_key(action, params or {}) if write_key else action
        if candidate in mod.WRITE:
            if not self._write_enabled(group):
                return (
                    f"指令组 {group} 的写操作未启用，请管理员打开 {group}_write 开关。"
                )
            if not is_admin:
                return "写操作需要管理员权限。"
        return None

    async def run(
        self,
        group: str,
        action: str,
        params: dict,
        *,
        user_key: str | None = None,
        is_admin: bool = False,
        sender: str = "",
        source: str = "command",
        umo: str = "",
    ) -> dict:
        err = self.check_permission(
            group,
            action,
            # bot_write: LLM 工具调用时机器人自身视为管理员（仅影响写操作校验）
            is_admin
            or (source == "tool" and bool(self.config.get("bot_write", False))),
            params,
        )
        if err:
            return {"ok": False, "error": err}
        params = dict(params)
        params.setdefault(
            "default_repo", normalize_default_repo(self.config.get("default_repo", ""))
        )
        logger.info(
            "gh 调用: group=%s action=%s source=%s repo=%r default_repo=%r",
            group,
            action,
            source,
            params.get("repo"),
            params.get("default_repo"),
        )
        if (
            action in LONG_TEXT_ACTIONS.get(group, set())
            and params.get("body") is not None
        ):
            params["body"] = apply_prefix(
                self.config.get("text_prefix", ""), params["body"], sender
            )
        client = GhClient(self.vault, user_key=user_key)
        try:
            data = await registry.run(client, group, action, params)
            result = {"ok": True, "data": data}
        except Exception as exc:  # noqa: BLE001 - gateway for all user-facing errors
            result = {"ok": False, "error": self.handle_error(exc)}
        self._record_audit(group, action, params, sender, source, umo, result)
        return result

    def _record_audit(self, group, action, params, sender, source, umo, result) -> None:
        if self.audit is None:
            return
        if not self.config.get("audit_enabled", True):
            return
        body = params.get("body")
        entry = {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "sender": sender or "",
            "umo": umo or "",
            "source": source,
            "group": group,
            "action": action,
            "repo": params.get("repo") or params.get("default_repo") or "",
            "params": sorted(k for k in params if k != "default_repo"),
            "body_preview": str(body) if body is not None else "",
            "ok": bool(result.get("ok")),
        }
        if not result.get("ok"):
            entry["error"] = str(result.get("error", ""))
        self.audit.record(entry)

    def format_result(self, group: str, data) -> str:
        mod = registry.get_group(group)
        return mod.format(data, self.list_limit(), self.content_limit())

    def list_limit(self) -> int:
        return min(max(int(self.config.get("list_limit", 10)), 1), 30)

    def content_limit(self) -> int:
        return max(int(self.config.get("content_limit", 1500)), 100)

    def handle_error(self, exc: Exception) -> str:
        if isinstance(exc, AuthError):
            return str(exc)
        if isinstance(exc, GhError):
            return str(exc)
        if isinstance(exc, RateLimitExceededException):
            return "GitHub API 速率限制已触发，请稍后再试。"
        if isinstance(exc, GithubException):
            status = exc.status
            if status in (401, 403):
                return "GitHub 认证失败，请检查 Token 是否有效及权限范围。"
            if status == 404:
                return "资源不存在，请检查仓库名/编号是否输入正确，或当前 Token 是否有权限。"
            if status == 422:
                return "请求参数不合法（HTTP 422）。"
            return f"GitHub API 错误 (HTTP {status}): {exc.data.get('message', '') if isinstance(exc.data, dict) else exc.data}"
        if isinstance(exc, ValueError):
            return str(exc)
        if isinstance(exc, KeyError):
            return str(exc)
        logger.exception("gh-cli 未预期错误")
        return f"发生未预期错误: {type(exc).__name__}。详见 AstrBot 日志。"
