from typing import Any, Dict, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """对话请求模型"""

    message: Optional[str] = None
    image_url: Optional[str] = None
    thread_id: str
    # 用户对 interrupt 节点的人工决策（如 send_email 的人机确认）
    interrupt_decision: Optional[Dict[str, Any]] = None
