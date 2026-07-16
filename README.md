# EduMate

EduMate 是一个面向校园学习场景的多智能体 RAG 学习助手。当前版本以“可演示、可迭代、不过度复杂”为原则，已经具备轻量多用户登录、PDF 知识库、公式提取策略、混合检索、课程问答、学习计划、复习任务和 Harness 检查体系。

## 当前进度

项目正在推进到 **Phase 10：集成测试与交付文档**。

已完成的核心能力：

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 用户系统 | 已完成 | 注册、登录、JWT、当前用户、用户级数据隔离 |
| 文档管理 | 已完成 | PDF 上传、列表、状态、删除、用户目录隔离 |
| PDF 处理 | 已完成 | 文本解析、层级分块、公式 LaTeX 规范化、低置信度不臆造 |
| 检索系统 | 已完成 | Qdrant 向量检索、BM25、RRF 混合检索 |
| RAG 问答 | 已完成 | 检索增强回答、引用来源、无密钥 placeholder 兜底 |
| 智能体 | 已完成 | MasterAgent 意图路由、KnowledgeAgent、PlannerAgent |
| 学习计划 | 已完成 | 生成多日计划并创建待办任务 |
| 复习系统 | 已完成 | 今日复习、评分、SM-2 间隔更新 |
| 前端 | 已完成 | 登录注册、资料、问答、聊天、任务、复习、计划 |
| Harness | 已完成 | 静态检查、API smoke、端到端演示链路脚本 |

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3, Vite, TypeScript |
| 后端 | FastAPI, SQLAlchemy, Alembic |
| 数据库 | PostgreSQL |
| 向量库 | Qdrant |
| LLM/Embedding | OpenAI-compatible API, 支持 DeepSeek 风格 base URL |
| 测试与评估 | pytest, PowerShell Harness, E2E runner |

## 服务地址

| 服务 | 默认地址 |
| --- | --- |
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| 后端 Swagger | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |

如果 8000 端口已经被其他项目占用，端到端 Harness 会通过 OpenAPI 预检提示“目标后端不是 EduMate”。这时需要关闭占用服务，或将 EduMate 后端启动到其他端口并设置 `EDUMATE_BASE_URL`。

## 快速启动

复制环境变量模板：

```bash
cp backend/.env.example backend/.env
```

启动基础服务和应用：

```bash
docker compose up -d
```

执行数据库迁移：

```bash
docker compose run --rm migrate
```

访问：

```text
Frontend: http://localhost:5173
Backend Docs: http://localhost:8000/docs
```

## 本地开发

后端：

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

前端生产构建：

```bash
cd frontend
npm run build
```

说明：项目在 Windows 环境下使用 `vite build --configLoader native`，用于避开 Vite 默认 config bundling 在部分本地路径权限下的读取问题。

## LLM 配置

项目通过 OpenAI-compatible 接口调用模型。测试阶段可以不配置真实密钥；未配置时，RAG/回答生成会进入 placeholder 兜底模式，便于继续验证业务链路。

OpenAI 示例：

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
```

DeepSeek 或其他兼容服务示例：

```env
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

Embedding 使用：

```env
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

## PDF 与公式策略

当前 PDF 模块不做复杂多模态图表识别，重点保证文字和公式处理可控：

| 项目 | 策略 |
| --- | --- |
| 可复制文字 | 直接解析并参与分块 |
| 公式文本 | 尽量规范化为标准 LaTeX |
| 公式图片 OCR | 预留轻量本地 OCR 开关 |
| 低置信度公式 | `FORMULA_OCR_MIN_CONFIDENCE < 0.7` 时不臆造 LaTeX |
| 图表 | 暂不识别，只保留后续扩展空间 |

相关环境变量：

```env
FORMULA_OCR_ENABLED=false
FORMULA_OCR_ENGINE=pix2tex
FORMULA_OCR_MIN_CONFIDENCE=0.7
```

## Harness 检查

后端测试建议在当前 Windows/Conda 环境禁用 pytest 插件自动加载，避免外部插件卡住启动：

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q backend\tests
```

常用 Harness：

```powershell
powershell -ExecutionPolicy Bypass -File harness\scripts\check_skeleton.ps1
powershell -ExecutionPolicy Bypass -File harness\scripts\check_auth_static.ps1
powershell -ExecutionPolicy Bypass -File harness\scripts\check_rag_static.ps1
powershell -ExecutionPolicy Bypass -File harness\scripts\check_frontend_chat_static.ps1
```

API smoke：

```powershell
powershell -ExecutionPolicy Bypass -File harness\scripts\check_api_smoke.ps1
```

端到端演示链路：

```powershell
powershell -ExecutionPolicy Bypass -File harness\scripts\check_e2e_demo_flow.ps1
```

启动 Docker 依赖、执行迁移、启动后端并运行完整 E2E：

```powershell
powershell -ExecutionPolicy Bypass -File harness\scripts\run_e2e_flow.ps1
```

已配置 `backend/.env` 后，运行一次真实模型连通性 smoke：

```powershell
powershell -ExecutionPolicy Bypass -File harness\scripts\run_llm_live_smoke.ps1
```

如果后端不是默认端口：

```powershell
$env:EDUMATE_BASE_URL="http://localhost:8001"
powershell -ExecutionPolicy Bypass -File harness\scripts\check_e2e_demo_flow.ps1
```

E2E 报告会写入：

```text
harness/reports/latest_e2e.json
```

## 项目结构

```text
backend/
  app/
    agents/       # MasterAgent, KnowledgeAgent, PlannerAgent
    core/         # 配置、安全、依赖、错误处理、日志
    models/       # SQLAlchemy 数据模型
    rag/          # PDF 解析、分块、Embedding、检索、Prompt
    routers/      # FastAPI API 路由
    schemas/      # Pydantic 请求和响应模型
    services/     # 业务服务层
  alembic/        # 数据库迁移
  tests/          # 后端测试和静态合约检查
  uploads/        # 本地上传文件，按 user_id 隔离

frontend/
  src/
    api/          # HTTP/SSE API 封装
    components/   # 聊天、资料、任务、复习、计划组件
    router/       # 预留前端路由
    stores/       # 预留状态管理
    views/        # 预留页面目录

harness/
  runners/        # Python 检查和 E2E runner
  scripts/        # PowerShell 入口
  reports/        # Harness 运行报告
```

更完整的架构说明见：

```text
EduMate — 代码架构图与目录职责.md
EduMate — 数据流图.md
EduMate — Harness 工程方案.md
EduMate — 项目实施计划（Plan）.md
```

## 常见问题

### 1. `localhost:8000` 不是 EduMate

如果 E2E 报告提示：

```text
Target backend does not look like EduMate
```

说明 8000 端口被其他 FastAPI 项目占用。关闭该服务，或用其他端口启动 EduMate 后端，并设置：

```powershell
$env:EDUMATE_BASE_URL="http://localhost:8001"
```

### 2. 没有配置 API key 能不能测试

可以。未配置 `OPENAI_API_KEY` / `OPENAI_MODEL` 时，回答生成会使用 placeholder 兜底。这样可以先验证登录、文档、检索、任务、复习、计划、前端交互等基础链路。

### 3. 前端 build 为什么使用 `--configLoader native`

这是为了适配当前 Windows 本地环境中 Vite 默认配置打包器读取上层目录权限失败的问题。`vue-tsc` 和 Vite native config loader 均已验证通过。

### 4. 后端日志怎么追踪请求

后端会为每个请求生成或透传 `X-Request-ID`，并记录请求完成、状态码、耗时和异常日志。错误响应会保留 `detail`，并附带：

```json
{
  "error": {
    "code": "not_found",
    "request_id": "..."
  }
}
```

## 下一步

Phase 10.5 将对照 PRD 做最终验收，检查当前版本的功能覆盖、已知限制和后续迭代清单。
