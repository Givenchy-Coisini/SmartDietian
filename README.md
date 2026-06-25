# SmartDietian（智能私厨）

基于 LangChain + LangGraph + Vue 3 的多模态 AI 智能营养师 Agent 实战项目。用户上传食材图片或文字描述，后端 Agent 自动识别食材、检索食谱，从营养价值与制作难度两个维度评分排序，以流式 SSE 的方式将结构化推荐报告渲染到前端。

## 核心特性

- **多模态识别**：上传食材图片，LLM 自动辨识并评估新鲜度与可用量
- **智能食谱搜索**：Agent 自动调用 Tavily 搜索引擎检索可行菜谱
- **多维度评分排序**：从营养价值和制作难度两个维度量化打分，简单又营养的排名靠前
- **结构化推荐报告**：包含食谱信息、得分、推荐理由的完整建议
- **流式对话**：基于 SSE（Server-Sent Events）的实时流式响应
- **会话管理**：多会话历史记录，可切换、删除历史会话；状态持久化到 Redis Checkpoint
- **国际化**：支持中英文界面切换（vue-i18n）
- **Markdown 渲染**：AI 回复自动渲染为格式化内容
- **提示词模板化**：使用 Jinja2 模板管理 Agent 系统提示词，便于版本化与迭代

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | >= 0.128.0 | Web 框架 |
| LangChain | >= 1.3.10 | LLM 应用框架 |
| LangGraph + Checkpoint Redis | >= 0.4.0 | Agent 状态图编排 + 会话记忆持久化 |
| langgraph-checkpoint-sqlite | >= 3.1.0 | 会话元数据 SQLite 存储 |
| langchain-tavily | >= 0.2.17 | Tavily 网络搜索工具 |
| langchain-openai / openai | >= 0.2.0 / >= 2.15.0 | DashScope OpenAI 兼容接入 |
| Jinja2 | >= 3.1.4 | Agent 提示词模板渲染 |
| Uvicorn | >= 0.40.0 | ASGI 服务器 |
| Redis Stack | latest | 向量存储 + RediSearch（LangGraph Checkpoint 依赖） |
| 阿里云 OSS v2 | >= 1.2.4 | 图片对象存储 |
| aiosqlite | >= 0.22.1 | 异步 SQLite 驱动 |
| python-dotenv | >= 1.2.2 | `.env` 加载 |

**LLM 模型**：通义千问 `qwen-vl-plus`（通过 DashScope OpenAI 兼容接口）

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.5.13 | 前端框架 |
| TypeScript | ~5.8.3 | 类型系统 |
| Vite | ^6.3.2 | 构建工具 |
| TailwindCSS | ^3.4.17 | 样式框架 |
| Pinia | ^3.0.2 | 状态管理 |
| vue-i18n | ^11.1.3 | 国际化 |
| axios | ^1.18.1 | HTTP 请求库（非流式接口） |
| Lucide Vue Next | ^0.474.0 | 图标库 |
| markdown-it | ^14.1.0 | Markdown 渲染 |

## 项目结构

```
SmartDietian/
├── app/                                # 后端应用
│   ├── agent/
│   │   ├── prompts/
│   │   │   └── personal_chief.j2       # 私厨 Agent 系统提示词模板（Jinja2）
│   │   ├── prompt_loader.py            # Jinja2 模板加载器，render_prompt() 入口
│   │   ├── personal_chief.py           # LangGraph Agent 核心（LLM、工具、记忆、流式输出）
│   │   └── email_agent.py              # 邮件 Agent（备用）
│   ├── api/
│   │   └── v1/
│   │       ├── chat.py                 # 对话接口（流式对话 / 历史消息 / 会话列表）
│   │       ├── oss.py                  # OSS 预签名上传 URL 接口
│   │       └── sessions.py             # 会话管理接口
│   ├── models/
│   │   ├── schemas.py                  # Pydantic 请求/响应模型
│   │   └── session.py                  # 会话元数据模型
│   ├── common/
│   │   └── logger.py                   # 日志配置
│   └── main.py                         # FastAPI 入口（CORS、路由、SPA fallback）
├── frontend/                           # 前端源码
│   ├── src/
│   │   ├── api/                        # API 调用层（基于 axios 工具类 + fetch SSE）
│   │   │   ├── chat.ts                 # 对话相关接口
│   │   │   └── oss.ts                  # OSS 预签名 + 直传
│   │   ├── utils/
│   │   │   └── request.ts              # axios 请求工具类（拦截器、统一错误处理）
│   │   ├── components/
│   │   │   ├── AppHeader.vue           # 顶部导航（含语言切换）
│   │   │   ├── AppChat.vue             # 主聊天区域（流式消息 + 图片上传）
│   │   │   ├── ChatSidebar.vue         # 历史会话侧边栏
│   │   │   ├── ChatMessage.vue         # 消息气泡（Markdown 渲染）
│   │   │   ├── ChatInput.vue           # 输入框（文本 + 图片选择）
│   │   │   └── ChatEmpty.vue           # 空状态引导
│   │   ├── composables/
│   │   │   ├── useChat.ts              # 会话管理逻辑
│   │   │   └── useImageUpload.ts       # 图片上传流程
│   │   ├── locales/                    # 国际化（zh-CN / en）
│   │   ├── assets/                     # 静态资源
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts                  # Vite 配置（5188 端口 + /api 代理 + build → app/static）
│   ├── tailwind.config.js
│   └── postcss.config.js
├── .env                                # 环境变量（不提交）
├── .gitignore
├── .python-version                     # 3.13
├── LICENSE
├── pyproject.toml                      # Python 项目配置
├── uv.lock                             # uv 依赖锁文件
└── README.md
```

## 系统架构

```
用户 → Vue 3 SPA (5188) → FastAPI (8001) → LangGraph Agent
                                              ├── Qwen-VL-Plus  （多模态 LLM）
                                              ├── Tavily Search （网络搜索）
                                              ├── Redis Stack   （会话记忆 / Checkpoint）
                                              ├── SQLite        （会话元数据）
                                              └── 阿里云 OSS    （图片存储）
```

### 数据流

1. 用户在前端输入食材描述或选择图片
2. 若包含图片，前端通过 `GET /api/v1/oss/presign` 拿到预签名 URL，再用 `axios.put` 直传到阿里云 OSS（不走后端中转）
3. 前端通过 `POST /api/v1/chat/stream` 以 SSE 发送对话请求
4. Agent 读取 `personal_chief.j2` 渲染系统提示词，再按 4 步流程处理：
   - 识别食材 → 搜索食谱 → 评分排序 → 输出结构化报告
5. 响应实时流式回传，前端做 Markdown 渲染
6. 会话状态写入 Redis Checkpoint，元数据落 SQLite，支持历史回顾

## 环境要求

- **Python**：>= 3.13（项目用 `uv` 管理，详见 `.python-version`）
- **Node.js**：>= 18（推荐 20.x，本仓库实测 v20.19.6 通过）
- **Redis Stack**：必须包含 RediSearch 模块（`langgraph-checkpoint-redis` 强依赖）
- **包管理器**：
  - Python：[`uv`](https://github.com/astral-sh/uv)（推荐）
  - Node.js：`npm`

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Givenchy-Coisini/SmartDietian.git
cd SmartDietian
```

### 2. 启动 Redis Stack

```bash
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
```

> 必须用 Redis Stack（自带 RediSearch），普通 Redis 启动后 Agent 初始化会失败。

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# 通义千问 API（DashScope OpenAI 兼容接口）
DASHSCOPE_API_KEY=your_dashscope_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Tavily 搜索 API
TAVILY_API_KEY=your_tavily_api_key

# 阿里云 OSS 配置
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_BUCKET=your_bucket_name

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 4. 启动后端

```bash
# 安装依赖（默认走清华源，见 pyproject.toml）
uv sync

# 启动开发服务器
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001
```

- 后端运行在 http://127.0.0.1:8001
- Swagger 文档：http://127.0.0.1:8001/docs
- 如需开发热重载可追加 `--reload`，但 reload 会派生子进程，多次启停时建议先 `Get-NetTCPConnection -LocalPort 8001` 确认端口已释放

### 5. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

- 前端开发服务器运行在 **http://localhost:5188/**
- Vite 已配置 `/api` 代理到 `http://127.0.0.1:8001`
- 端口在 `frontend/vite.config.ts` 中通过 `server.port = 5188 + strictPort = true` 锁定

### 6. 生产构建

```bash
# 构建前端（输出到 app/static/）
cd frontend && npm run build

# 启动生产服务器（不带 reload）
cd .. && uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

构建后的前端静态文件由后端 `main.py` 的 SPA fallback 路由托管，单端口即可访问完整应用。

## API 接口

基础 URL：`http://127.0.0.1:8001/api/v1`

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat/stream` | 流式对话（SSE），支持文本 + 图片多模态输入 |
| GET | `/chat/messages?thread_id=xxx` | 获取指定会话的历史消息 |
| DELETE | `/chat/messages?thread_id=xxx` | 删除指定会话 |
| GET | `/chat/threads` | 获取所有会话列表 |

#### 流式对话请求示例

```json
{
  "message": "这些食材可以做什么菜？",
  "image_url": "https://bucket.oss-cn-beijing.aliyuncs.com/food.jpg",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 文件上传

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/oss/presign?filename=food.jpg` | 获取 OSS 预签名上传 URL |

返回 `uploadUrl`（客户端直传用）和 `accessUrl`（图片访问地址）。

### 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sessions` | 列出所有会话元数据 |
| DELETE | `/sessions/{thread_id}` | 删除指定会话 |

## Agent 工作流程

```
用户输入（食材图片 / 文字）
    │
    ▼
┌─────────────────────────────┐
│ 0. 加载 Jinja2 提示词模板    │
│    prompts/personal_chief.j2 │
├─────────────────────────────┤
│ 1. 识别和评估食材            │
│    辨识可见食材，评估新鲜度  │
│    整理「当前可用食材清单」  │
├─────────────────────────────┤
│ 2. 智能食谱检索              │
│    调用 Tavily 搜索食谱      │
├─────────────────────────────┤
│ 3. 多维度评估排序            │
│    营养价值 + 制作难度打分   │
│    简单营养的排名靠前        │
├─────────────────────────────┤
│ 4. 结构化方案输出            │
│    食谱信息 / 得分 / 推荐理由│
└─────────────────────────────┘
    │
    ▼
SSE 流式输出 → 前端 Markdown 渲染
```

## 核心模块说明

### Agent 提示词模板（`app/agent/prompts/personal_chief.j2`）

- 使用 Jinja2 语法，支持变量注入与条件分支
- 通过 `prompt_loader.render_prompt("personal_chief.j2", **context)` 在 Agent 初始化时一次性渲染
- `StrictUndefined` 配合 `is defined` 守卫，避免漏传上下文时静默失败
- 修改提示词不需要改 Python 代码，直接编辑 `.j2` 即可

### Agent 主流程（`app/agent/personal_chief.py`）

- 基于 LangChain `create_agent` 构建
- 使用 **Qwen-VL-Plus** 多模态模型，支持图文输入
- 集成 **Tavily Search** 作为网络搜索工具
- 通过 **RedisSaver** 实现 LangGraph Checkpoint 会话持久化
- 支持 `stream_mode="messages"` 逐 token 流式输出

### 前端 axios 工具类（`frontend/src/utils/request.ts`）

- 统一 `baseURL` 与超时
- 请求拦截器自动注入 `Authorization`（如有 token）
- 响应拦截器把 `response.data` 解包，业务代码只关心数据本体
- 暴露泛型 `request<T>(config): Promise<T>`，类型友好
- **流式接口（SSE）仍走原生 `fetch + ReadableStream`**，因为 axios-xhr 无法增量读取响应体

### 前端会话管理（`useChat.ts` + `ChatSidebar.vue`）

- 自动生成 UUID 作为 `thread_id`，存储在 localStorage
- 支持多会话切换、历史消息懒加载
- 侧边栏展示所有会话预览，支持删除
- 流式响应期间可通过 `AbortController` 中断

### 图片上传（`useImageUpload.ts` + `oss.ts`）

- 选择图片后本地预览
- `getPresignUrl` → `uploadToOss`（裸 `axios.put`，绕开拦截器避免破坏 OSS 签名）
- 上传完成后返回 HTTPS URL，随对话请求发送给 Agent

## 开发指南

### Git 提交规范（建议）

参照 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: 新功能
fix: 修复
docs: 文档更新
refactor: 重构
style: 格式调整
chore: 构建/工具配置
```

### Windows 控制台中文 commit message

PowerShell 默认 GBK，直接 `git commit -m "中文"` 会乱码。推荐：

```powershell
# 把中文写到 UTF-8 文件
Set-Content -Path .git/COMMIT_MSG_TMP -Value "feat: 中文提交说明" -Encoding utf8
git commit -F .git/COMMIT_MSG_TMP
Remove-Item .git/COMMIT_MSG_TMP
```

## 常见问题

**Q: 后端启动报 `redis.exceptions.ConnectionError: Error 10061`？**
A: 本机 6379 端口没有 Redis 服务。先 `docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest`，再 `Test-NetConnection -ComputerName 127.0.0.1 -Port 6379` 确认连通后再启后端。

**Q: 后端启动报 RediSearch 相关错误？**
A: 必须使用 **Redis Stack**（含 RediSearch 模块），原生 `redis:latest` 不行。

**Q: `vite.config.ts` 编辑器里 `path` / `__dirname` 飘红？**
A: 安装 Node 类型声明：`npm add -D @types/node@^20`，VS Code 重启 TS Server 即可。

**Q: 前端开发时 API 请求 404 / ECONNREFUSED？**
A: 检查后端是否已在 8001 端口监听，Vite 代理 `/api → 127.0.0.1:8001` 才会生效。

**Q: 图片上传失败 `SignatureDoesNotMatch`？**
A: 上传到 OSS 必须用裸 `axios.put`（见 `oss.ts`），不能走带拦截器的封装实例，否则 `Authorization` 头与 `baseURL` 会破坏签名。

## 许可证

[MIT License](./LICENSE)

## 致谢
- 模型：通义千问（DashScope）
- 搜索：Tavily

---

⭐ 如果这个项目对你有帮助，欢迎 Star 支持！
