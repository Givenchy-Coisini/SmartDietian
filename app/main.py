import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.v1 import chat, oss, sessions
from app.common.logger import setup_logging

setup_logging()

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="SmartDietian API",
    description="智能私厨：识别食材，推荐菜谱，多模态对话",
    version="0.1.0",
)

# 1. CORS：浏览器 / 浏览器扩展前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 业务路由
app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(oss.router, prefix="/api/v1", tags=["OSS 上传签名"])
app.include_router(sessions.router, prefix="/api/v1", tags=["会话管理"])

# 3. 前端静态资源（SPA fallback）
static_dir = os.path.join(os.path.dirname(__file__), "static")


@app.get("/{path:path}", include_in_schema=False)
async def serve_frontend(path: str):
    """SPA fallback：API 路径直接 404，否则尝试静态文件，最后回落到 index.html"""
    if path.startswith("api/"):
        return JSONResponse({"error": "Not Found"}, status_code=404)

    file_path = os.path.join(static_dir, path)
    if path and os.path.isfile(file_path):
        return FileResponse(file_path)

    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"message": "SmartDietian 后端已上线，前端尚未构建。", "status": "ok"}


if __name__ == "__main__":
    import uvicorn

    # 启动命令：python -m app.main
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)
