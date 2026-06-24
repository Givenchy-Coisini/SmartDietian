"""人机协同邮件助理示例。

说明：本模块完整复刻自参考项目，演示了 LangGraph 中的：
- 动态工具（基于 state 切换可用工具集合）
- 动态系统提示词
- HumanInTheLoopMiddleware（如 send_email 需要人工确认）
- AsyncSqliteSaver Checkpoint（与 personal_chief 的 RedisSaver 区分）

当前并未在 ``app/main.py`` 中挂载任何 API 路由，仅作为可被后续按需启用的能力沉淀。
"""

import json
import os
from typing import Callable

import aiosqlite
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelRequest,
    ModelResponse,
    dynamic_prompt,
    wrap_model_call,
)
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command

from app.common.logger import logger

AUTHENTICATED_KEY = "authenticated"


# ==================== State ====================
class AuthenticatedState(AgentState):
    """额外记录用户是否已鉴权"""

    authenticated: bool


# ==================== Tools ====================
@tool
def authenticate(email: str, password: str, runtime: ToolRuntime) -> Command:
    """Authenticate the user with the given email and password."""

    authenticated = False
    message = "Authentication failed"

    if email == "huge@itcast.cn" and password == "123":
        authenticated = True
        message = "Successfully authenticated"

    return Command(
        update={
            "authenticated": authenticated,
            "messages": [ToolMessage(message, tool_call_id=runtime.tool_call_id)],
        }
    )


@tool
def check_inbox() -> list[dict]:
    """Read emails from the inbox."""
    return [
        {
            "subject": "周末见个面？",
            "content": """
                嗨 帅哥，
                我下周会去城里，不知道我们有没有机会一起喝杯咖啡？

                祝好，简
            """,
            "from": "jane@itcast.cn",
            "status": "unread",
        },
        {
            "subject": "周五会议",
            "content": """
                嗨 帅哥，
                非常抱歉，我周五的会议无法准时参加了，能不能重新安排个时间？

                祝好，小李
            """,
            "from": "lixiaolong@itcast.cn",
            "status": "checked",
        },
    ]


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send a response email."""
    return f"邮件已发送至 {to} , 主题： {subject} , 内容： {body}"


# ==================== Middleware：动态工具 / 动态提示词 ====================
@wrap_model_call
async def dynamic_tool_call(
    request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """仅在用户已鉴权时开放 check_inbox / send_email"""

    authenticated = request.state.get(AUTHENTICATED_KEY)
    tools = [check_inbox, send_email] if authenticated else [authenticate]
    request = request.override(tools=tools)
    return await handler(request)


authenticated_prompt = "You are a helpful assistant that can check the inbox and send emails."
unauthenticated_prompt = """You are a helpful email assistant.
    For system security protocols, you must authenticate user before any other interaction.
    """


@dynamic_prompt
def dynamic_prompt_func(request: ModelRequest) -> str:
    """根据是否鉴权返回不同的系统提示词"""
    authenticated = request.state.get(AUTHENTICATED_KEY)
    return authenticated_prompt if authenticated else unauthenticated_prompt


# ==================== Helper ====================
def _serialize(obj):
    """递归转换为可 JSON 序列化的对象"""
    if hasattr(obj, "value"):
        return _serialize(obj.value)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


# ==================== EmailAgent ====================
class EmailAgent:
    """异步邮件 Agent，使用 SQLite 作为 LangGraph checkpoint"""

    def __init__(self) -> None:
        self.conn: aiosqlite.Connection | None = None
        self.checkpointer: BaseCheckpointSaver | None = None
        self.agent = None

    async def init(self) -> None:
        await self.init_checkpointer()
        logger.info("checkpointer 初始化完成 ....")
        await self.init_agent()
        logger.info("email agent 初始化完成 ....")

    async def init_checkpointer(self) -> None:
        os.makedirs("./db", exist_ok=True)
        self.conn = await aiosqlite.connect("./db/mail_fiend.db")
        logger.info("sqlite connection 完成 ....")
        self.checkpointer = AsyncSqliteSaver(conn=self.conn)
        await self.checkpointer.setup()

    async def close(self) -> None:
        if self.conn is not None:
            await self.conn.close()
            logger.info("sqlite connection 关闭 ....")

    async def init_agent(self) -> None:
        self.agent = create_agent(
            "deepseek-chat",
            tools=[authenticate, check_inbox, send_email],
            state_schema=AuthenticatedState,
            checkpointer=self.checkpointer,
            middleware=[
                dynamic_tool_call,
                dynamic_prompt_func,
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "authenticate": False,
                        "check_inbox": False,
                        "send_email": True,
                    }
                ),
            ],
        )

    # ---------- SSE 流式响应 ----------
    async def generate_sse(self, thread_id: str, message: str, interrupt_decision: dict):
        """生成 SSE 事件流"""
        config = {"configurable": {"thread_id": thread_id}}

        _input: dict | Command = {"messages": [HumanMessage(content=message)]}
        if interrupt_decision:
            _input = Command(resume={"decisions": [interrupt_decision]})

        logger.info(f"调用 email agent，Input：{_input}")
        try:
            async for chunk in self.agent.astream(
                _input,
                config=config,
                stream_mode=["messages", "updates"],
                version="v2",
            ):
                event_type = chunk["type"]
                data = chunk["data"]

                if event_type == "messages":
                    token, _metadata = data
                    content = None
                    if isinstance(token, AIMessage) and hasattr(token, "content"):
                        content = token.content
                    if content:
                        yield {
                            "event": "message",
                            "data": json.dumps(
                                {"type": "message", "content": content},
                                ensure_ascii=False,
                            ),
                        }

                elif event_type == "updates":
                    if "__interrupt__" in data:
                        interrupt_data = data["__interrupt__"]
                        details = _serialize(interrupt_data)
                        yield {
                            "event": "interrupt",
                            "data": json.dumps(
                                {
                                    "type": "interrupt",
                                    "interrupt": {
                                        "reason": "需要人工确认",
                                        "details": details,
                                    },
                                },
                                ensure_ascii=False,
                                default=str,
                            ),
                        }

            yield {
                "event": "done",
                "data": json.dumps(
                    {"type": "done", "content": "处理完成"},
                    ensure_ascii=False,
                ),
            }

        except Exception as e:
            logger.error(f"SSE 流中断: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps(
                    {"type": "error", "error": str(e)},
                    ensure_ascii=False,
                ),
            }

    async def get_messages(self, thread_id: str) -> dict:
        """获取会话历史，并在存在中断时附带中断信息"""
        logger.info(f"获取历史消息，thread_id: {thread_id}")

        config = {"configurable": {"thread_id": thread_id}}
        state = await self.agent.aget_state(config)
        if state is None or not state.values:
            return {"messages": []}

        messages = state.values.get("messages", [])

        result: list[dict[str, str]] = []
        for msg in messages:
            if not msg.content:
                continue
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})

        response: dict = {"messages": result}

        interrupts = None
        if hasattr(state, "interrupts") and state.interrupts:
            interrupts = state.interrupts
        elif hasattr(state, "tasks") and state.tasks:
            for task in state.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    interrupts = task.interrupts
                    break

        if interrupts:
            response["has_interrupt"] = True
            response["interrupt"] = {
                "reason": "需要人工确认",
                "details": _serialize(interrupts),
            }

        return response

    async def clear_messages(self, thread_id: str) -> None:
        config = {"configurable": {"thread_id": thread_id}}
        await self.checkpointer.adelete(config)


email_agent = EmailAgent()

__all__ = ["email_agent"]
