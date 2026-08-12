from pathlib import Path

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.api.web import error_response, file_response, json_response, request
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from . import tools as gh_tools
from .core.audit import AuditLog
from .core.command import build_help, parse_command
from .core.config_ingest import ingest_tokens
from .core.executor import Executor
from .core.vault import Vault

PLUGIN_NAME = "astrbot_plugin_gh_cli"


@register("astrbot_plugin_gh_cli", "astrbot-gh-cli", "GitHub CLI 插件", "1.0.0")
class GhCliPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config or {}
        self.vault: Vault | None = None
        self.executor: Executor | None = None
        self.audit: AuditLog | None = None

    async def initialize(self):
        data_dir = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        self.vault = Vault(data_dir)
        changes = ingest_tokens(self.config, self.vault)
        if changes:
            self.config.update(changes)
            if hasattr(self.config, "save_config"):
                self.config.save_config()
        self.audit = AuditLog(data_dir, limit=int(self.config.get("audit_limit", 1000)))
        self.executor = Executor(self.config, self.vault, audit=self.audit)
        self.context.add_llm_tools(*gh_tools.build_tools(self.executor))
        self._register_web_apis()

    def _register_web_apis(self):
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/audit/list",
            self.page_audit_list,
            ["GET"],
            "审计日志列表",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/audit/clear",
            self.page_audit_clear,
            ["POST"],
            "清空审计日志",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/audit/export",
            self.page_audit_export,
            ["GET"],
            "导出审计日志",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/audit/stats",
            self.page_audit_stats,
            ["GET"],
            "审计统计",
        )

    async def page_audit_list(self):
        if self.audit is None:
            return error_response("审计日志未初始化", status_code=500)
        sender = request.query.get("sender", "")
        group = request.query.get("group", "")
        ok_raw = request.query.get("ok")
        ok = None
        if ok_raw in ("true", "1"):
            ok = True
        elif ok_raw in ("false", "0"):
            ok = False
        limit = request.query.get("limit", 200, type=int)
        return json_response(self.audit.list_entries(sender, group, ok, limit))

    async def page_audit_clear(self):
        if self.audit is None:
            return error_response("审计日志未初始化", status_code=500)
        if not request.username:
            return error_response("需要登录 Dashboard", status_code=403)
        self.audit.clear()
        return json_response({"cleared": True})

    async def page_audit_export(self):
        if self.audit is None:
            return error_response("审计日志未初始化", status_code=500)
        entries = self.audit.list_entries(limit=1000)
        path = (
            Path(get_astrbot_data_path())
            / "plugin_data"
            / self.name
            / "audit_export.json"
        )
        path.write_text(
            __import__("json").dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return file_response(
            path,
            filename="audit.json",
            content_type="application/json",
        )

    async def page_audit_stats(self):
        if self.audit is None:
            return error_response("审计日志未初始化", status_code=500)
        return json_response(self.audit.stats())

    @filter.command("gh")
    async def gh(self, event: AstrMessageEvent):
        """GitHub CLI: /gh <指令组> <操作> [参数]"""
        text = event.message_str.strip()
        if text.startswith("/gh"):
            text = text[3:].strip()
        try:
            if not text or text == "help":
                yield event.plain_result(build_help())
                return
            if text.startswith("auth "):
                yield event.plain_result(
                    await self._handle_auth(event, text[5:].strip())
                )
                return
            group, action, params = parse_command(text)
        except ValueError as exc:
            yield event.plain_result(str(exc))
            return
        if not action:
            yield event.plain_result(
                f"用法: /gh {group} <操作>。输入 /gh help 查看帮助。"
            )
            return
        params.setdefault("default_repo", self.config.get("default_repo", ""))
        user_key = f"{event.get_platform_id()}:{event.get_sender_id()}"
        result = await self.executor.run(
            group,
            action,
            params,
            user_key=user_key,
            is_admin=event.is_admin(),
            sender=event.get_sender_name(),
            umo=event.unified_msg_origin,
        )
        if not result["ok"]:
            yield event.plain_result(f"❌ {result['error']}")
            return
        yield event.plain_result(self.executor.format_result(group, result["data"]))

    async def _handle_auth(self, event: AstrMessageEvent, sub: str) -> str:
        user_key = f"{event.get_platform_id()}:{event.get_sender_id()}"
        if sub.startswith("use "):
            name = sub[4:].strip()
            if not name:
                return "用法: /gh auth use <名称>"
            if not self.vault.get_personal_token(name):
                return (
                    f"❌ 不存在名为 {name} 的个人 Token（请管理员在插件配置中录入）。"
                )
            self.vault.set_binding(user_key, name)
            return f"✅ 已切换身份到 {name}。"
        if sub == "status":
            binding = self.vault.get_binding(user_key)
            if binding:
                return f"当前身份: {binding}（个人 Token）"
            if self.vault.get_shared_token():
                return "当前身份: 共享 Token"
            return "尚未配置任何 Token。"
        return "用法: /gh auth use <名称> | /gh auth status"

    async def terminate(self):
        pass
