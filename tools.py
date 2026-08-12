"""LLM tools: one FunctionTool per command group."""

import json

from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from .core.executor import Executor
from .core.tool_schemas import TOOL_SCHEMAS


def _make_tool_class(tool_name: str, schema: dict):
    @dataclass(config=ConfigDict(arbitrary_types_allowed=True))
    class _Base(FunctionTool[AstrAgentContext]):
        name: str = Field(default=tool_name)
        description: str = Field(default=schema["description"])
        parameters: dict = Field(default_factory=lambda: schema["parameters"])
        executor: Executor = Field(default=None, repr=False)

        async def call(
            self, context: ContextWrapper[AstrAgentContext], **kwargs
        ) -> ToolExecResult:
            event = context.context.event
            action = kwargs.get("action", "")
            sender_name = kwargs.pop("sender_name", None) or event.get_sender_name()
            umo = kwargs.pop("umo", None) or event.unified_msg_origin
            params = {k: v for k, v in kwargs.items() if k != "action"}
            user_key = f"{event.get_platform_id()}:{event.get_sender_id()}"
            result = await self.executor.run(
                self.name.removeprefix("gh_"),
                action,
                params,
                user_key=user_key,
                is_admin=event.is_admin(),
                sender=sender_name,
                source="tool",
                umo=umo,
            )
            if not result["ok"]:
                return result["error"]
            return json.dumps(result["data"], ensure_ascii=False)

    return type(f"GhTool{tool_name}", (_Base,), {})


def build_tools(executor: Executor) -> list[FunctionTool]:
    return [
        _make_tool_class(name, schema)(executor=executor)
        for name, schema in TOOL_SCHEMAS.items()
    ]
