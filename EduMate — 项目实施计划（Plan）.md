# EduMate — 项目实施计划（Plan）

> **目标读者**：开发者 / AI 编码助手（如 Codex）  
> **使用方式**：按阶段推进。每个阶段完成后先对照验收标准检查，再进入下一阶段。  
> **当前迭代重点**：在原有 RAG 学习助手基础上加入轻量多用户与登录注册，同时保持系统边界清晰。

---

## 1. 项目概述

| 项目 | 说明 |
| --- | --- |
| 项目名称 | EduMate — 多智能体校园学习助手 |
| 技术栈 | Vue 3 + FastAPI + PostgreSQL + Qdrant + OpenAI API |
| 核心目标 | 实现轻量多用户、三智能体协作、课件 RAG 问答、学习计划管理 |
| 开发周期预估 | 9-12 周（按每周 10-15 小时计算） |
| 当前版本原则 | 先做稳定可演示版本，再逐步增强体验和智能化 |

---

## 2. 阶段总览

| 阶段 | 名称 | 预估时间 | 核心产出 |
| --- | --- | --- | --- |
| Phase 1 | 项目初始化与基础设施 | 第 1 周 | Docker Compose、项目骨架、基础配置 |
| Phase 2 | 用户认证与数据模型 | 第 2 周 | 注册登录、JWT、用户表、业务表迁移 |
| Phase 3 | 基础业务 API | 第 3 周 | 文档、待办、复习池基础 CRUD |
| Phase 4 | PDF 解析与层级化分块 | 第 4 周 | PDF 文本提取、分块、元数据生成 |
| Phase 5 | 向量化入库与混合检索 | 第 5-6 周 | Embedding、Qdrant、BM25、RRF |
| Phase 6 | RAG 问答与 SSE | 第 7 周 | 带引用的流式问答 |
| Phase 7 | 主智能体意图识别与路由 | 第 8 周 | 5 类意图识别、任务分发、兜底 |
| Phase 8 | 规划智能体与 SM-2 | 第 9 周 | 计划生成、自然语言待办、复习算法 |
| Phase 9 | 前端完整实现 | 第 10-11 周 | 登录页、主界面、聊天、文档、待办 |
| Phase 10 | 集成测试与交付文档 | 第 12 周 | E2E 测试、README、最终验收 |
| Phase H | Harness 工程贯穿 | 全阶段 | 启动检查、API 冒烟、用户隔离、RAG/智能体评估 |

---

## 3. 实施原则

- **轻量认证**：只做普通用户注册登录，不做角色权限、组织、多租户后台。
- **数据隔离优先**：所有业务数据必须有 `user_id`，所有查询必须按当前用户过滤。
- **RAG 是核心亮点**：PDF 分块、混合检索、引用来源是项目简历价值的重点。
- **先可用后增强**：PDF 标题识别、自然语言待办更新可以逐步优化，但接口和数据结构要提前留好。
- **可演示优先**：每个阶段都要能跑起来、能说明成果。
- **Harness 贯穿**：关键功能不只实现，还要配套可重复运行的检查脚本、样例数据和评估集。

---

## 4. 详细任务清单

### Phase 1：项目初始化与基础设施

**目标**：搭建完整开发环境，确保基础服务可启动。

**任务清单**

- [ ] 1.1 创建项目目录结构 `backend/`、`frontend/`
- [ ] 1.2 编写 `docker-compose.yml`
  - PostgreSQL：端口 `5432`
  - Qdrant：端口 `6333`
  - 后端服务：端口 `8000`
  - 前端服务：端口 `5173`
- [ ] 1.3 创建后端骨架
  - `app/main.py`：FastAPI 应用入口，注册路由、中间件和健康检查
  - `app/db.py`：数据库连接、Session 管理、SQLAlchemy Base
  - `app/core/`：配置、安全、鉴权依赖等基础能力
  - `app/models/`：SQLAlchemy 表模型
  - `app/schemas/`：Pydantic 请求/响应模型
  - `app/routers/`：HTTP API 路由层
  - `app/services/`：业务服务层，编排数据库、文件、LLM 等操作
  - `app/agents/`：Master、Knowledge、Planner 三个智能体
  - `app/rag/`：PDF 解析、分块、Embedding、向量检索、BM25、RRF
  - `uploads/`：上传文件目录，按 `user_id` 分目录保存
  - `tests/`：后端测试目录
- [ ] 1.4 创建前端 Vue 3 + Vite 项目
  - `src/main.ts`：前端入口
  - `src/App.vue`：根组件
  - `src/router/`：页面路由和登录守卫
  - `src/api/`：API 封装，统一处理 JWT 和错误
  - `src/stores/`：用户状态、文档状态、待办状态
  - `src/views/`：Login、Register、Home 页面
  - `src/components/`：聊天、文档管理、待办、复习等组件
- [ ] 1.5 编写 `.env.example`
- [ ] 1.6 验证 FastAPI、Vue、PostgreSQL、Qdrant 可启动

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| Docker Compose | 所有基础服务启动成功 |
| FastAPI | 访问 `/docs` 显示 Swagger |
| Vue | `npm run dev` 可访问前端页面 |
| PostgreSQL | 可连接并创建数据库 |
| Qdrant | 控制台可访问 |

---

### Phase 2：用户认证与数据模型

**目标**：实现轻量登录注册，并建立多用户数据隔离基础。

**任务清单**

- [ ] 2.1 安装后端依赖
  - `sqlalchemy`
  - `alembic`
  - `asyncpg`
  - `psycopg2-binary`
  - `python-jose` 或等价 JWT 库
  - `passlib[bcrypt]`
  - `pydantic-settings`
- [ ] 2.2 实现配置模块 `app/core/config.py`
- [ ] 2.3 实现安全模块 `app/core/security.py`
  - 密码哈希
  - 密码校验
  - JWT 生成与解析
- [ ] 2.4 创建 SQLAlchemy 模型
  - `User`
  - `Document`
  - `Task`
  - `ReviewSchedule`
- [ ] 2.5 所有业务表增加 `user_id`
- [ ] 2.6 配置 Alembic 并生成首次迁移
- [ ] 2.7 实现认证依赖 `get_current_user`
- [ ] 2.8 实现认证 API
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `GET /api/auth/me`

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| 注册 | 新用户写入 `users` 表，密码为哈希 |
| 登录 | 返回 JWT 和用户信息 |
| 当前用户 | 携带 token 可访问 `/api/auth/me` |
| 未登录访问业务接口 | 返回 401 |
| 数据模型 | `documents`、`tasks`、`review_schedule` 均包含 `user_id` |

---

### Phase 3：基础业务 API

**目标**：完成文档、待办、复习池的基础 CRUD，并保证用户隔离。

**任务清单**

- [ ] 3.1 实现文档 API
  - `GET /api/documents`
  - `POST /api/documents/upload`
  - `GET /api/documents/{task_id}/status`
  - `DELETE /api/documents/{id}`
- [ ] 3.2 实现待办 API
  - `GET /api/tasks`
  - `POST /api/tasks`
  - `PUT /api/tasks/{id}`
  - `DELETE /api/tasks/{id}`
- [ ] 3.3 实现复习池 API
  - `GET /api/review/today`
  - `POST /api/review`
  - `PUT /api/review/{id}/rate`
- [ ] 3.4 上传文件保存到当前用户目录，例如 `uploads/{user_id}/`
- [ ] 3.5 编写基础 API 测试

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| 文档上传 | 返回 `task_id`，文件保存到用户目录 |
| 文档列表 | 只返回当前用户文档 |
| 待办 CRUD | 当前用户可新增、查看、修改、删除待办 |
| 用户隔离 | 用户 A 无法访问用户 B 的数据 |
| 复习池 | 可添加知识点并查询今日复习 |

---

### Phase 4：PDF 解析与层级化分块

**目标**：实现 RAG 的文档处理基础。

**任务清单**

- [ ] 4.1 安装 `pymupdf`、`tiktoken`
- [ ] 4.2 实现 `app/rag/parser.py`
  - 提取每页文本
  - 捕获标题候选
  - 记录页码、字体大小等可用特征
- [ ] 4.3 实现 `app/rag/chunker.py`
  - 按标题路径分块
  - 目标长度约 500 tokens
  - 输出统一 chunk 结构
- [ ] 4.4 实现后台处理流程 `document_service.py`
  - `pending` → `processing`
  - 解析成功后更新分块数量
  - 失败时记录错误
- [ ] 4.5 用示例 PDF 编写单元测试

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| PDF 解析 | 能提取可复制文本 |
| 分块输出 | 每个 chunk 包含 `user_id`、`doc_id`、`path`、`text` |
| 块大小 | 主要块落在 300-700 tokens |
| 状态更新 | 文档状态正确流转 |

---

### Phase 5：向量化入库与混合检索

**目标**：实现可用且带用户隔离的检索系统。

**任务清单**

- [ ] 5.1 安装 `openai`、`qdrant-client`、BM25 相关库
- [ ] 5.2 实现 `app/rag/embedding.py`
  - 单条 Embedding
  - 批量 Embedding
  - 重试与错误处理
- [ ] 5.3 实现 `app/rag/vector_store.py`
  - 创建 `knowledge_chunks`
  - 批量 upsert
  - 按 `user_id` 过滤检索
  - 按 `user_id + doc_id` 删除
- [ ] 5.4 实现 `app/rag/retriever.py`
  - Qdrant top-10
  - BM25 top-10
  - RRF 融合 top-5
- [ ] 5.5 将上传处理串联为：解析 → 分块 → Embedding → Qdrant
- [ ] 5.6 编写检索测试

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| Embedding | 文本成功生成 1536 维向量 |
| Qdrant 入库 | payload 包含 `user_id` 和完整文档元数据 |
| 用户隔离检索 | 用户 A 查询不到用户 B 的向量 |
| Hybrid Search | 能返回语义和关键词相关的 chunks |
| 删除文档 | PostgreSQL 与 Qdrant 数据同步删除 |

---

### Phase 6：RAG 问答与 SSE

**目标**：实现带引用来源的流式课件问答。

**任务清单**

- [ ] 6.1 实现 `app/rag/prompt_builder.py`
- [ ] 6.2 实现 `app/services/llm_service.py`
  - 非流式调用
  - 流式调用
  - 3 次重试
- [ ] 6.3 实现 `app/agents/knowledge_agent.py`
- [ ] 6.4 实现 `/api/chat` SSE 响应
  - `start`
  - `content`
  - `citations`
  - `done`
  - `error`
- [ ] 6.5 实现无文档、无结果、LLM 失败兜底

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| RAG 问答 | 返回与课件相关的答案 |
| 引用来源 | 答案末尾包含章节路径 |
| SSE | 前端可逐步接收内容 |
| 无结果 | 返回友好提示 |
| 未登录 | `/api/chat` 返回 401 |

---

### Phase 7：主智能体意图识别与路由

**目标**：让聊天入口具备任务分发能力。

**任务清单**

- [ ] 7.1 实现 `app/agents/master_agent.py`
- [ ] 7.2 定义 5 类意图
  - `knowledge_query`
  - `plan_create`
  - `plan_query`
  - `plan_update`
  - `general_chat`
- [ ] 7.3 使用 GPT-4o-mini 或规则+LLM 混合方式输出 `{intent, entities, confidence}`
- [ ] 7.4 实现低置信度澄清
- [ ] 7.5 接入 `KnowledgeAgent` 和 `PlannerAgent`

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| 知识问题 | 路由到知识库智能体 |
| 计划创建 | 路由到规划智能体 |
| 待办查询 | 返回当前用户待办 |
| 日常问候 | 主智能体直接回复 |
| 低置信度 | 反问用户澄清 |

---

### Phase 8：规划智能体与 SM-2

**目标**：完成学习规划能力闭环。

**任务清单**

- [ ] 8.1 实现 `app/services/task_service.py`
- [ ] 8.2 实现 `app/services/review_service.py`
  - 添加知识点
  - 今日复习查询
  - 根据评分更新 EF 和下次复习日期
- [ ] 8.3 实现 `app/agents/planner_agent.py`
  - 计划生成
  - 自动创建待办
  - 待办查询
  - 简单自然语言更新
- [ ] 8.4 实现 `POST /api/plan/generate`
- [ ] 8.5 编写规划智能体测试

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| 计划生成 | 返回计划文本并创建待办 |
| 待办查询 | 只返回当前用户待办 |
| 自然语言创建 | “帮我添加待办...”可创建任务 |
| SM-2 | 评分后更新复习间隔 |
| 今日复习 | 返回当前用户应复习知识点 |

---

### Phase 9：前端完整实现

**目标**：实现可演示的完整 Web 应用。

**任务清单**

- [ ] 9.1 实现认证页面
  - 登录
  - 注册
  - 退出
  - token 保存与请求拦截
- [ ] 9.2 实现主布局
  - 顶部栏
  - 左侧边栏
  - 主聊天区
- [ ] 9.3 实现聊天组件
  - SSE 接收
  - Markdown 渲染
  - 引用来源展示
- [ ] 9.4 实现文档管理组件
  - 上传
  - 状态轮询
  - 删除
- [ ] 9.5 实现待办组件
  - 列表
  - 添加
  - 勾选完成
  - 删除
- [ ] 9.6 实现 API 封装
  - `authApi`
  - `chatApi`
  - `documentApi`
  - `taskApi`
  - `reviewApi`

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| 未登录 | 自动进入登录页 |
| 登录后 | 进入主应用并显示用户名 |
| 文档上传 | 上传后可看到处理状态 |
| 课件问答 | 能看到流式回答和引用 |
| 待办 | 可增删改查和勾选完成 |

---

### Phase 10：集成测试与交付文档

**目标**：完成端到端验证，确保项目可稳定演示。

**任务清单**

- [ ] 10.1 编写后端测试
  - 注册登录
  - 用户隔离
  - 文档 API
  - 待办 API
  - 复习 API
- [ ] 10.2 编写端到端测试
  - 注册用户 A 和用户 B
  - 用户 A 上传 PDF
  - 用户 B 无法看到用户 A 文档
  - 用户 A 提问并得到引用答案
  - 创建计划并生成待办
- [ ] 10.3 完善错误处理与日志
- [ ] 10.4 完善 README
- [ ] 10.5 最终对照 PRD 验收

**验收标准**

| 验收项 | 预期结果 |
| --- | --- |
| Docker Compose | 一键启动成功 |
| 认证测试 | 注册、登录、鉴权通过 |
| 用户隔离测试 | 所有跨用户访问被阻止 |
| RAG 测试 | 上传 PDF 后可问答 |
| PRD 验收 | 核心验收项全部通过 |

---

## 5. 风险与应对

| 风险 | 影响 | 应对措施 |
| --- | --- | --- |
| 多用户导致复杂度上升 | 开发周期变长 | 只做 JWT + `user_id` 隔离，不做角色权限 |
| PDF 标题识别不稳定 | 分块质量波动 | 先实现可用启发式规则，后续迭代优化 |
| OpenAI API 费用超支 | 开发成本增加 | 开发阶段尽量使用小模型，设置预算上限 |
| Qdrant 用户隔离遗漏 | 数据泄露风险 | 所有检索和删除必须强制带 `user_id` filter |
| SSE 前端处理复杂 | 体验不稳定 | 先实现最小可用流式，再加错误提示和重试 |
| 时间不足 | 无法全部完成 | 优先级：认证与隔离 > RAG 问答 > 前端演示 > SM-2 增强 |

---

## 6. 里程碑

| 里程碑 | 完成时间目标 | 关键交付物 |
| --- | --- | --- |
| M1：基础设施就绪 | 第 1 周末 | Docker Compose、前后端骨架 |
| M2：账号体系可用 | 第 2 周末 | 注册登录、JWT、用户隔离模型 |
| M3：基础业务闭环 | 第 3 周末 | 文档、待办、复习池 CRUD |
| M4：PDF 可入库检索 | 第 6 周末 | PDF 分块、Embedding、Qdrant、Hybrid Search |
| M5：RAG 问答可用 | 第 7 周末 | 流式回答、引用来源 |
| M6：三智能体集成 | 第 9 周末 | Master、Knowledge、Planner 联通 |
| M7：项目可演示 | 第 12 周末 | 前端完整、测试通过、README 完整 |

---

## 7. 开发规范

### 后端规范

| 项目 | 要求 |
| --- | --- |
| Python | Python 3.10+ |
| 风格 | 使用 `ruff` 格式化 |
| 类型 | 关键函数保留类型注解 |
| 配置 | 使用 `pydantic-settings` |
| 密钥 | 只允许环境变量注入 |
| 数据访问 | 所有业务查询必须绑定当前 `user_id` |
| 错误格式 | API 错误保持统一结构 |

### 前端规范

| 项目 | 要求 |
| --- | --- |
| 框架 | Vue 3 + Composition API |
| 写法 | 推荐 `<script setup>` |
| 状态 | 可使用 Pinia 管理用户和业务状态 |
| 请求 | API 层统一封装 token 注入和 401 处理 |
| 样式 | 桌面端优先，界面保持清晰克制 |

### Git 提交建议

```text
feat(auth): add jwt login and registration
feat(rag): add qdrant vector search
feat(planner): add sm2 review scheduling
fix(chat): handle sse stream errors
docs(prd): update multi-user requirements
```
