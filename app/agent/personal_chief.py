import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_tavily import TavilySearch
from langgraph.checkpoint.redis import RedisSaver

from app.common.logger import logger

# 加载环境变量
load_dotenv()

# ==================== 工具：Tavily Web 搜索 ====================
tavily = TavilySearch(
    max_results=5,
    topic="general",
)


# ==================== 多模态 LLM ====================
model = init_chat_model(
    model=os.getenv("DASHSCOPE_MODEL", "qwen-vl-plus"),
    model_provider="openai",
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
)


# ==================== Redis Checkpoint ====================
redis_password = os.getenv("REDIS_PASSWORD", "")
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6379)
# Redis Search 只能在 db 0 上创建索引
redis_db = 0

if redis_password:
    REDIS_URL = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
else:
    REDIS_URL = f"redis://{redis_host}:{redis_port}/{redis_db}"

checkpointer = RedisSaver(REDIS_URL)
# 自动创建 Redis Search 索引等结构
checkpointer.setup()


# ==================== 系统提示词 ====================
system_prompt = """
你是一名私人厨师。收到用户提供的食材照片或清单后，请按以下流程操作：
1.识别和评估食材：若用户提供照片，首先辨识所有可见食材。基于食材的外观状态，评估其新鲜度与可用量，整理出一份"当前可用食材清单"。
2.智能食谱检索：优先调用 web_search 工具，以"可用食材清单"为核心关键词，查找可行菜谱。
3.多维度评估与排序：从营养价值和制作难度两个维度对检索到的候选食谱进行量化打分，并根据得分排序，制作简单且营养丰富的排名靠前。
4.结构化方案输出：把排序后的食谱整理为一份结构清晰的建议报告，要包含食谱信息、得分、推荐理由、食谱的参考图片，帮助用户快速做出决策。

请严格按照流程，优先调用 web_search 工具搜索食谱，搜索不到的情况下才能自己发挥。
"""

# ==================== Agent ====================
agent = create_agent(
    model=model,
    tools=[tavily],
    checkpointer=checkpointer,
    system_prompt=system_prompt,
)


# ==================== 业务方法 ====================
async def search_recipes(prompt: str, image: str, thread_id: str):
    """调用 agent 搜索食谱，流式返回 token"""
    logger.info(f"[用户]: {prompt}, image: {image}, thread_id: {thread_id}")
    try:
        if not image or image.strip() == "":
            message = HumanMessage(content=prompt)
        else:
            message = HumanMessage(
                content=[
                    {"type": "image", "url": image},
                    {"type": "text", "text": prompt},
                ]
            )

        for chunk, _metadata in agent.stream(
            {"messages": [message]},
            {"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield chunk.content

    except Exception as e:
        logger.error(f"\n[错误]: {e}")
        yield "信息检索失败，试试看手动输入食物列表？"


def clear_messages(thread_id: str) -> None:
    """清空指定会话的历史"""
    logger.info(f"清空历史消息，thread_id: {thread_id}")
    checkpointer.delete_thread(thread_id)


def get_messages(thread_id: str) -> list[dict[str, str]]:
    """获取会话历史"""
    logger.info(f"获取历史消息，thread_id: {thread_id}")

    checkpoint = checkpointer.get({"configurable": {"thread_id": thread_id}})
    if not checkpoint:
        return []

    channel_values = checkpoint.get("channel_values")
    if not channel_values:
        return []

    messages = channel_values.get("messages", [])
    if not messages:
        return []

    result: list[dict[str, str]] = []
    for msg in messages:
        if not msg.content:
            continue

        if isinstance(msg, HumanMessage):
            # 多模态消息：content 是 list，提取文本和图片
            if isinstance(msg.content, list):
                text_parts: list[str] = []
                image_url = None
                for part in msg.content:
                    if part.get("type") == "text":
                        text_parts.append(part["text"])
                    elif part.get("type") == "image":
                        image_url = part.get("url")
                entry: dict[str, str] = {"role": "user", "content": " ".join(text_parts)}
                if image_url:
                    entry["image_url"] = image_url
                result.append(entry)
            else:
                result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})

    return result


def list_threads() -> list[dict[str, str]]:
    """获取所有会话列表，返回每个会话的 thread_id 与首条用户消息预览"""
    logger.info("获取所有会话列表")

    import redis as redis_lib

    r = redis_lib.Redis(
        host=redis_host,
        port=int(redis_port),
        db=0,
        password=redis_password or None,
    )

    thread_ids: set[str] = set()
    try:
        offset = 0
        batch = 100
        while True:
            result = r.execute_command(
                "FT.SEARCH",
                "checkpoint",
                "*",
                "RETURN",
                "1",
                "thread_id",
                "LIMIT",
                str(offset),
                str(batch),
            )
            count = result[0]
            for i in range(1, len(result), 2):
                fields = result[i + 1]
                for j in range(0, len(fields), 2):
                    if fields[j].decode() == "thread_id":
                        thread_ids.add(fields[j + 1].decode())
            offset += batch
            if offset >= count:
                break
    except Exception as e:
        logger.error(f"查询 checkpoint 索引失败: {e}")
        return []

    threads: list[dict[str, str]] = []
    for tid in thread_ids:
        msgs = get_messages(tid)
        preview = ""
        for msg in msgs:
            if msg.get("role") == "user":
                preview = msg.get("content", "")[:50]
                break
        if preview:
            threads.append({"thread_id": tid, "preview": preview})

    return threads
