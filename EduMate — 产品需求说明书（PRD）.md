# EduMate — 产品需求说明书（PRD）

> **目标读者**：开发者 / AI 编码助手（如 Codex）  
> **文档定位**：这是项目实现的功能合同。开发时应优先满足本文档定义的范围、接口、数据模型与验收标准。  
> **当前版本目标**：在不复杂化系统的前提下，实现一个支持轻量登录注册、多用户数据隔离、PDF 课件问答、学习规划与间隔重复复习的校园学习助手。

---

## 1. 产品概述

**产品名称**：EduMate — 多智能体校园学习助手  
**目标用户**：在校大学生、自学者、需要管理课件与复习任务的学习者  
**核心价值**：把“课件知识检索”和“学习计划执行”放到同一个学习工作台中，让用户可以上传自己的 PDF 课件，围绕课件提问，并通过待办和复习计划持续推进学习。

EduMate 不是简单的 ChatGPT 套壳，而是由三个智能体协作完成学习场景：

| 智能体 | 职责 | 主要输入 | 主要输出 |
| --- | --- | --- | --- |
| 主智能体（Master） | 识别用户意图并进行任务路由 | 用户聊天消息 | 意图 JSON、澄清问题、路由结果 |
| 知识库智能体（Knowledge） | 管理 PDF 课件知识库并执行 RAG 问答 | PDF 文档、用户问题 | 带引用来源的答案 |
| 规划智能体（Planner） | 管理待办、生成学习计划、维护复习节奏 | 学习目标、待办指令、复习反馈 | 待办列表、复习计划、今日复习项 |

---

## 2. 版本范围

### 2.1 当前版本必须实现

- 轻量用户注册、登录、退出和当前用户信息查询
- 基于 JWT 的会话鉴权
- 多用户数据隔离：每个用户只能访问自己的文档、待办、复习计划和向量数据
- PDF 上传、解析、层级化分块、Embedding 入库
- Qdrant 向量检索 + BM25 关键词检索 + RRF 融合排序
- 基于课件内容的 RAG 问答，答案附带引用来源
- 主智能体意图识别与路由
- 待办 CRUD、学习计划生成、SM-2 简化版间隔重复
- Vue 桌面端 Web 界面
- Docker Compose 本地一键启动

### 2.2 当前版本明确不做

- 复杂权限系统、管理员后台、班级/组织/团队空间
- 第三方 OAuth 登录、短信登录、邮箱验证、找回密码邮件流程
- 聊天历史持久化
- PDF 中图片、手写内容、复杂表格和公式的 OCR 识别
- 跨文档知识图谱或自动关系推理
- 移动端深度适配
- 语音输入/输出
- 用户反馈评分系统
- 在线支付、订阅、用量计费

> 设计原则：支持多用户，但不做“企业级账号系统”。只实现学习助手需要的最小认证与数据隔离能力。

---

## 3. 用户与认证

### 3.1 用户角色

当前版本只有一种角色：**普通用户**。

每个用户拥有独立的数据空间：

- 自己上传的 PDF
- 自己的文档向量
- 自己的待办任务
- 自己的复习知识点
- 自己的计划生成结果

### 3.2 FR-01：用户注册

- 用户可使用 `username`、`email`、`password` 注册账号
- `username` 和 `email` 必须唯一
- 密码不允许明文存储，必须使用安全哈希算法存储，例如 `bcrypt`
- 注册成功后可直接返回登录态，或提示用户登录。推荐注册成功后自动登录，以减少操作步骤

请求示例：

```json
{
  "username": "student01",
  "email": "student01@example.com",
  "password": "password123"
}
```

### 3.3 FR-02：用户登录

- 用户可使用 `email + password` 登录
- 登录成功后返回 `access_token`
- 前端将 token 保存在 `localStorage` 或内存状态中，并在后续请求中通过 `Authorization: Bearer <token>` 发送
- 登录失败时返回友好错误，不暴露“邮箱是否存在”等敏感细节

### 3.4 FR-03：当前用户与退出

- 前端可调用 `/api/auth/me` 获取当前用户信息
- 退出登录由前端清除 token 完成
- 后端当前版本不维护 token 黑名单

### 3.5 认证边界

- 除注册、登录、健康检查外，所有业务 API 必须要求登录
- 所有数据库查询必须按 `user_id` 过滤
- Qdrant payload 必须包含 `user_id`，检索和删除时必须带上 `user_id` 过滤条件

---

## 4. 通用聊天界面

### FR-04：发送消息

- 用户在输入框中输入自然语言文本，点击发送或按 Enter 提交
- 前端调用 `/api/chat`
- 后端通过主智能体识别意图，并路由到对应智能体
- 响应以 **SSE（Server-Sent Events）流式** 返回，前端逐字渲染
- 聊天历史仅保存在前端内存中，页面刷新后清空

### FR-05：意图分类

主智能体必须识别以下 5 类意图：

| 意图标识 | 触发示例 | 路由目标 |
| --- | --- | --- |
| `knowledge_query` | “课件里讲了什么？”、“解释一下最大似然估计” | 知识库智能体 |
| `plan_create` | “帮我规划高数复习计划”、“安排今天的学习” | 规划智能体 |
| `plan_query` | “我今天有什么待办？”、“我的复习计划是什么？” | 规划智能体 |
| `plan_update` | “把明天的复习改成下午 3 点”、“标记高数已完成” | 规划智能体 |
| `general_chat` | “你好”、“介绍一下你自己”、“你能做什么？” | 主智能体直接回复 |

主智能体输出必须是结构化 JSON：

```json
{
  "intent": "knowledge_query",
  "entities": {
    "topic": "最大似然估计"
  },
  "confidence": 0.91
}
```

- 若 `confidence < 0.6`，主智能体应反问用户澄清意图
- 意图识别失败时，按 `general_chat` 兜底，但不要编造课件内容

### FR-06：错误兜底

- 若识别为 `knowledge_query` 但当前用户未上传任何 PDF，回复：“你还没有上传课件，请先上传 PDF 文件后再提问。”
- 若识别为 `plan_query` 但当前用户无待办数据，回复：“你目前没有待办事项，需要我帮你规划学习任务吗？”
- 若 token 失效，前端跳转到登录页或显示登录弹窗

---

## 5. 知识库智能体

### 5.1 PDF 上传与处理

### FR-07：上传 PDF

- 前端提供“上传课件”入口，仅接受 `.pdf`
- 文件大小限制：最大 50MB
- 上传后后端立即返回 `task_id`
- 前端轮询 `/api/documents/{task_id}/status` 获取处理状态
- 同一用户可上传多个 PDF，同一用户的所有文档共同参与检索
- 不同用户之间的文档、向量和检索结果必须隔离

### FR-08：PDF 解析与层级化分块

- 使用 `pymupdf` 解析 PDF 可提取文本
- 优先识别标题层级，按标题边界进行层级化分块
- 单块目标长度约 500 tokens，允许 300-700 tokens 的弹性范围
- 超长块按段落或语义边界继续切分，并保留标题路径

每个文本块必须包含以下元数据：

```json
{
  "user_id": "uuid",
  "doc_id": "uuid",
  "filename": "高数第3章.pdf",
  "chapter": "第3章",
  "section": "3.1 导数",
  "path": "第3章 > 3.1 导数",
  "text": "块正文内容...",
  "chunk_index": 0
}
```

### FR-09：向量化入库

- 对每个文本块调用 Embedding 模型生成 1536 维向量
- 将向量和 payload 写入 Qdrant
- payload 必须包含 `user_id` 和 `doc_id`
- 处理完成后，将文档状态更新为 `done`，并记录 `total_chunks`
- 处理失败时，将文档状态更新为 `failed`，并记录 `error_message`

### FR-10：文档管理

- 前端展示当前用户的文档列表：文件名、上传时间、分块数量、处理状态
- 支持删除文档
- 删除文档时必须同步删除 Qdrant 中 `user_id + doc_id` 对应的所有向量

### 5.2 RAG 问答

### FR-11：知识检索

当用户问题被路由到知识库智能体时，执行以下流程：

1. 将用户问题向量化
2. 使用 Qdrant 按 `user_id` 过滤，检索语义相似 top-10 文本块
3. 使用 BM25 在当前用户的文本块中检索 top-10
4. 使用 RRF（Reciprocal Rank Fusion）融合排序，输出 top-5
5. 组装带来源的上下文
6. 调用 LLM 生成答案
7. 通过 SSE 返回内容，并在末尾返回引用来源

上下文格式：

```text
[来源：第3章 > 3.1 导数]
正文内容...
```

Prompt 模板：

```text
你是一个学习助手。请根据以下课件内容回答用户的问题。
如果内容不足以回答问题，请如实说“课件中未找到相关信息”。

【课件内容】
{context}

【用户问题】
{question}

请给出准确、简洁的回答，并在回答末尾附上引用来源（章节名称）。
```

### FR-12：无结果处理

若检索到的文本块相关性低，回复：

> 在已上传的课件中未找到与你问题相关的内容。建议你上传更多相关课件或换个方式提问。

---

## 6. 规划智能体

### 6.1 待办管理

### FR-13：查看待办

- 用户可通过聊天输入“查看我的待办”或在界面中查看待办列表
- 默认展示当前用户未完成待办
- 支持按完成状态和截止日期筛选

待办字段：

- `id`
- `user_id`
- `title`
- `subject`
- `priority`（1-5）
- `due_date`
- `is_done`
- `created_at`

### FR-14：创建待办

- 用户输入“帮我添加待办：复习高数第 3 章，明天截止”，系统解析并创建待办
- 若缺少必要信息，例如标题，系统反问补充
- 支持聊天创建，也支持前端表单直接创建

### FR-15：更新待办

- 支持修改标题、科目、优先级、截止日期和完成状态
- 用户说“把复习高数改成后天”，系统识别并更新对应待办
- 若匹配到多个可能待办，系统应要求用户进一步确认

### FR-16：删除待办

- 用户可通过界面删除待办
- 用户也可通过自然语言删除，例如“删除高数待办”
- 删除操作只影响当前用户的数据

### 6.2 复习计划生成

### FR-17：生成计划

- 用户输入“帮我规划高数第 3 章的复习计划，我有 3 天时间”
- 系统调用 LLM 将目标拆解为每日子任务
- 生成计划后自动创建对应待办

计划格式示例：

```text
【复习计划：高数第3章】
Day 1（2026-07-16）：阅读 3.1-3.2，做课后题 1-5
Day 2（2026-07-17）：阅读 3.3，做课后题 6-10
Day 3（2026-07-18）：总复习，做模拟题
```

### FR-18：SM-2 间隔重复

- 用户可以手动添加知识点到复习池
- 后续版本可从 PDF 中自动提取知识点；当前版本可作为增强项，不作为最低验收阻塞项
- 每个知识点记录名称、科目、下次复习日期、间隔天数、难易度因子
- 用户每次复习后评价掌握程度（1-5 分）
- 系统根据评分更新 EF 值、间隔天数和下次复习日期

---

## 7. 前端界面要求

### FR-19：认证界面

- 未登录用户默认进入登录页
- 登录页提供注册入口
- 注册表单包含用户名、邮箱、密码
- 登录表单包含邮箱、密码
- 登录成功后进入主应用
- 顶部显示当前用户名和退出按钮

### FR-20：主界面布局

- 左侧边栏：文档列表、上传入口、待办概览
- 右侧主区域：聊天界面
- 顶部栏：应用名称、当前状态、当前用户、退出入口
- 桌面端优先，移动端只需保证基本可用，不做深度优化

### FR-21：聊天交互

- 用户消息右对齐，AI 消息左对齐
- AI 回复通过 SSE 逐步显示
- 支持 Markdown 渲染
- RAG 回答末尾展示引用来源
- 引用来源至少展示章节路径，后续可扩展点击定位

### FR-22：文档上传

- 支持拖拽上传或点击选择文件
- 上传时展示进度或处理中状态
- 文档列表展示处理状态：`pending`、`processing`、`done`、`failed`

### FR-23：待办视图

- 以列表形式展示今日待办和未完成待办
- 支持勾选完成/取消完成
- 支持新增、编辑、删除待办

---

## 8. 非功能需求

| 编号 | 需求 | 标准 |
| --- | --- | --- |
| NFR-01 | 响应时间 | 意图识别 < 1s，RAG 问答首字 < 3s，完整输出 < 15s |
| NFR-02 | 数据隔离 | 所有业务数据按 `user_id` 隔离，禁止跨用户访问 |
| NFR-03 | 安全性 | 密码哈希存储，业务 API 需要 JWT 鉴权，密钥通过环境变量注入 |
| NFR-04 | 错误容忍 | LLM API 超时/限流自动重试 3 次，失败后返回友好提示 |
| NFR-05 | 可维护性 | 代码按 `routers/`、`services/`、`agents/`、`rag/`、`models/` 组织 |
| NFR-06 | 数据持久化 | PostgreSQL 和 Qdrant 数据卷挂载，重启不丢失 |
| NFR-07 | 本地可运行 | 除 LLM API 外，系统应能通过 Docker Compose 在本地启动 |

---

## 9. 数据模型

### 9.1 PostgreSQL 表

**users**

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**documents**

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    total_chunks INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**tasks**

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(64),
    priority INT DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    due_date DATE,
    is_done BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**review_schedule**

```sql
CREATE TABLE review_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    knowledge_point VARCHAR(255) NOT NULL,
    subject VARCHAR(64),
    interval_days INT DEFAULT 1,
    next_review_date DATE NOT NULL,
    ease_factor FLOAT DEFAULT 2.5,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 9.2 Qdrant Collection

| 属性 | 值 |
| --- | --- |
| Collection 名称 | `knowledge_chunks` |
| 向量维度 | 1536 |
| 距离度量 | Cosine |
| Payload 字段 | `user_id`、`doc_id`、`filename`、`chapter`、`section`、`path`、`text`、`chunk_index` |

---

## 10. API 接口规格

### 10.1 认证接口

**POST** `/api/auth/register`

```json
{
  "username": "student01",
  "email": "student01@example.com",
  "password": "password123"
}
```

**POST** `/api/auth/login`

```json
{
  "email": "student01@example.com",
  "password": "password123"
}
```

响应：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "student01",
    "email": "student01@example.com"
  }
}
```

**GET** `/api/auth/me`

返回当前登录用户信息。

### 10.2 聊天接口

**POST** `/api/chat`

请求头：

```text
Authorization: Bearer <token>
```

请求体：

```json
{
  "message": "解释一下最大似然估计"
}
```

响应：`text/event-stream`

```text
data: {"type": "start", "intent": "knowledge_query"}
data: {"type": "content", "text": "最大似然估计是一种..."}
data: {"type": "citations", "sources": ["第2章 > 2.1 最大似然估计"]}
data: {"type": "done"}
```

### 10.3 文档接口

- **POST** `/api/documents/upload`
- **GET** `/api/documents/{task_id}/status`
- **GET** `/api/documents`
- **DELETE** `/api/documents/{id}`

所有文档接口必须要求登录，且只操作当前用户的数据。

### 10.4 待办接口

- **GET** `/api/tasks?is_done=false`
- **POST** `/api/tasks`
- **PUT** `/api/tasks/{id}`
- **DELETE** `/api/tasks/{id}`

### 10.5 复习计划接口

- **POST** `/api/plan/generate`
- **GET** `/api/review/today`
- **POST** `/api/review`
- **PUT** `/api/review/{id}/rate`

---

## 11. 技术栈

| 层级 | 技术 | 版本/说明 |
| --- | --- | --- |
| 前端 | Vue 3 + Vite | Vue 3.x |
| 前端 UI | Element Plus 或 Naive UI | 二选一即可 |
| 后端 | FastAPI | Python 3.10+ |
| ORM | SQLAlchemy + Alembic | 数据模型与迁移 |
| 认证 | JWT + bcrypt/passlib | 轻量登录注册 |
| 向量数据库 | Qdrant | Docker 部署 |
| 关系数据库 | PostgreSQL | 15+ |
| LLM（意图识别） | GPT-4o-mini | 可配置 |
| LLM（RAG 问答） | GPT-4o | 可配置 |
| Embedding | `text-embedding-3-small` | 1536 维 |
| PDF 解析 | `pymupdf` | 提取文本与标题特征 |
| 部署 | Docker Compose | 本地一键启动 |

---

## 12. 验收标准

| 场景 | 预期行为 |
| --- | --- |
| 用户注册 | 使用用户名、邮箱、密码注册成功，密码不明文存储 |
| 用户登录 | 登录成功返回 JWT，后续业务接口可携带 token 访问 |
| 未登录访问业务接口 | 返回 401，前端提示登录 |
| 多用户数据隔离 | 用户 A 看不到用户 B 的文档、待办、复习知识点和检索结果 |
| 上传 PDF | 显示处理状态，完成后状态变为 `done` |
| 上传失败 | 非 PDF 或超过 50MB 返回明确错误 |
| 课件问答 | 检索当前用户课件，流式返回答案并附带章节引用 |
| 未上传 PDF 时提问 | 提示用户先上传课件 |
| 生成复习计划 | 返回结构化计划，并自动创建待办 |
| 查询今日待办 | 返回当前用户今日待办列表 |
| 日常问候 | 主智能体直接回复，不调用 RAG |
| 无待办查询 | 返回“暂无待办”类友好提示 |

---

## 13. 项目结构

```text
edumate/
├── backend/                         # FastAPI 后端服务，承载认证、业务 API、智能体与 RAG
│   ├── app/                         # 后端应用主包
│   │   ├── main.py                  # FastAPI 入口，注册中间件、路由、健康检查
│   │   ├── db.py                    # 数据库连接、Session 管理、Base 声明
│   │   ├── core/                    # 横切基础能力：配置、安全、鉴权依赖
│   │   │   ├── config.py            # 环境变量配置，如数据库、OpenAI、JWT、Qdrant
│   │   │   ├── security.py          # 密码哈希、密码校验、JWT 生成与解析
│   │   │   └── deps.py              # FastAPI 依赖，如 get_current_user、get_db
│   │   ├── models/                  # SQLAlchemy 数据库模型
│   │   │   ├── user.py              # users 表模型
│   │   │   ├── document.py          # documents 表模型，绑定 user_id
│   │   │   ├── task.py              # tasks 表模型，绑定 user_id
│   │   │   └── review.py            # review_schedule 表模型，绑定 user_id
│   │   ├── schemas/                 # Pydantic 请求/响应模型
│   │   │   ├── auth.py              # 注册、登录、当前用户响应结构
│   │   │   ├── document.py          # 文档上传、状态、列表响应结构
│   │   │   ├── task.py              # 待办创建、更新、响应结构
│   │   │   └── review.py            # 复习知识点、评分响应结构
│   │   ├── routers/                 # API 路由层，只处理 HTTP 入参、鉴权和响应
│   │   │   ├── auth.py              # /api/auth/register、login、me
│   │   │   ├── chat.py              # /api/chat，SSE 流式聊天入口
│   │   │   ├── documents.py         # /api/documents，上传、列表、状态、删除
│   │   │   ├── tasks.py             # /api/tasks，待办 CRUD
│   │   │   ├── plan.py              # /api/plan/generate，学习计划生成
│   │   │   └── review.py            # /api/review，今日复习与评分
│   │   ├── services/                # 业务服务层，负责用例编排和数据库操作
│   │   │   ├── auth_service.py      # 用户注册、登录校验、用户查询
│   │   │   ├── document_service.py  # 文件保存、文档状态流转、后台处理调度
│   │   │   ├── task_service.py      # 待办创建、查询、更新、删除
│   │   │   ├── review_service.py    # SM-2 复习计划计算与复习池管理
│   │   │   └── llm_service.py       # OpenAI 调用封装、流式输出、重试逻辑
│   │   ├── agents/                  # 智能体层，负责自然语言任务理解与分发
│   │   │   ├── master_agent.py      # 主智能体：意图识别、置信度、路由分发
│   │   │   ├── knowledge_agent.py   # 知识库智能体：调用 RAG 检索与问答
│   │   │   └── planner_agent.py     # 规划智能体：计划生成、待办自然语言操作
│   │   └── rag/                     # RAG 核心模块，尽量保持可独立测试
│   │       ├── parser.py            # PDF 文本提取、标题候选识别
│   │       ├── chunker.py           # 层级化分块、token 长度控制
│   │       ├── embedding.py         # Embedding 生成与批处理
│   │       ├── vector_store.py      # Qdrant Collection、upsert、filter search、delete
│   │       ├── bm25_store.py        # BM25 关键词索引与检索
│   │       ├── retriever.py         # Hybrid Search + RRF 融合排序
│   │       └── prompt_builder.py    # RAG 上下文拼装与 Prompt 模板
│   ├── alembic/                     # 数据库迁移脚本目录
│   ├── uploads/                     # 本地上传文件目录，按 user_id 分目录保存
│   ├── tests/                       # 后端单元测试与接口测试
│   ├── requirements.txt             # Python 依赖清单
│   └── .env.example                 # 后端环境变量示例
├── frontend/                        # Vue 3 前端应用
│   ├── src/
│   │   ├── App.vue                  # 前端根组件
│   │   ├── main.ts                  # Vue 应用入口，注册插件、路由、状态管理
│   │   ├── router/                  # 前端路由与登录守卫
│   │   ├── api/                     # 后端 API 调用封装
│   │   │   ├── client.ts            # fetch/axios 客户端，自动附带 JWT
│   │   │   ├── auth.ts              # 登录、注册、当前用户
│   │   │   ├── chat.ts              # SSE 聊天请求
│   │   │   ├── documents.ts         # 文档上传、列表、删除、状态查询
│   │   │   ├── tasks.ts             # 待办 CRUD
│   │   │   └── review.ts            # 复习池与评分接口
│   │   ├── stores/                  # 前端状态管理
│   │   │   ├── auth.ts              # token、当前用户、登录状态
│   │   │   └── app.ts               # 文档、待办、全局状态
│   │   ├── views/                   # 页面级组件
│   │   │   ├── LoginView.vue        # 登录页
│   │   │   ├── RegisterView.vue     # 注册页
│   │   │   └── HomeView.vue         # 主工作台页面
│   │   └── components/              # 可复用 UI 组件
│   │       ├── AppShell.vue         # 顶部栏 + 左侧栏 + 主内容布局
│   │       ├── ChatPanel.vue        # 聊天消息、输入框、SSE 渲染
│   │       ├── DocumentManager.vue  # 文档上传、状态列表、删除
│   │       ├── TodoList.vue         # 待办列表、勾选、编辑、删除
│   │       └── ReviewPanel.vue      # 今日复习、评分入口
│   └── package.json                 # 前端依赖与脚本
├── docker-compose.yml               # PostgreSQL、Qdrant、后端、前端的一键编排
├── README.md                        # 项目说明、启动方式、演示说明
└── docs/                            # 可选：后续沉淀设计文档、接口说明、演示材料
```

---

## 14. 运行命令

```bash
# 启动所有服务
docker-compose up -d

# 后端开发模式
cd backend
uvicorn app.main:app --reload

# 前端开发模式
cd frontend
npm run dev
```
