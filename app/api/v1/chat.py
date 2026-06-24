from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.personal_chief import (
    clear_messages,
    get_messages,
    list_threads,
    search_recipes,
)
from app.models.schemas import ChatRequest

router = APIRouter()


@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """流式对话"""
    return StreamingResponse(
        search_recipes(request.message, request.image_url, request.thread_id),
        media_type="text/event-stream",
    )


@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """获取历史消息"""
    messages = get_messages(thread_id)
    return {"messages": messages}


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """清空历史消息"""
    clear_messages(thread_id)
    return {"success": True}


@router.get("/chat/threads")
async def get_chat_threads():
    """获取所有会话列表"""
    threads = list_threads()
    return {"threads": threads}
