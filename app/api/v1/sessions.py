from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.agent.personal_chief import clear_messages, get_messages
from app.models.session import (
    SessionCreate,
    SessionResponse,
    create_session,
    delete_session,
    get_sessions,
)

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse, tags=["会话"])
def create_new_session(session: SessionCreate):
    """创建新会话"""
    return create_session(session)


@router.get("/sessions", response_model=List[SessionResponse], tags=["会话"])
def list_sessions(
    user_id: Optional[str] = Query(None, description="用户ID"),
    biz_type: Optional[str] = Query(None, description="业务类型"),
):
    """查询会话列表，支持按 user_id 和 biz_type 筛选"""
    return get_sessions(user_id=user_id, biz_type=biz_type)


@router.delete("/sessions/{thread_id}", tags=["会话"])
async def remove_session(thread_id: str):
    """删除会话及其 LangGraph checkpoint"""
    deleted = delete_session(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    clear_messages(thread_id)
    return {"message": "Session deleted successfully"}


@router.get("/sessions/{thread_id}/messages", tags=["会话"])
async def get_session_messages(thread_id: str):
    """获取会话的历史消息"""
    try:
        messages = get_messages(thread_id)
        return {"messages": messages}
    except Exception as e:
        return {"messages": [], "error": str(e)}
