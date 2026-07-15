# EduMate — 数据流图

> **文档用途**：说明 EduMate 中核心数据如何在前端、后端、智能体、RAG、数据库和外部模型之间流动。  
> **阅读方式**：先看总体数据流，再看登录、PDF 入库、课件问答、学习计划四条核心链路。

---

## 1. 总体数据流图

```mermaid
flowchart LR
    User["用户"]
    Frontend["Vue 前端\n页面 / 组件 / 状态 / API 封装"]
    AuthAPI["认证 API\n/api/auth/*"]
    ChatAPI["聊天 API\n/api/chat\nSSE"]
    DocAPI["文档 API\n/api/documents/*"]
    TaskAPI["学习 API\n/api/tasks\n/api/plan\n/api/review"]

    AuthService["AuthService\n注册 / 登录 / 当前用户"]
    MasterAgent["MasterAgent\n意图识别 / 路由"]
    KnowledgeAgent["KnowledgeAgent\n课件问答"]
    PlannerAgent["PlannerAgent\n计划 / 待办 / 复习"]
    DocumentService["DocumentService\n上传 / 处理 / 状态"]
    TaskService["TaskService\n待办 CRUD"]
    ReviewService["ReviewService\nSM-2 复习"]

    Parser["PDF Parser\n文本提取"]
    Chunker["Chunker\n层级化分块"]
    Embedding["Embedding\n文本向量化"]
    Retriever["Retriever\n向量检索 + BM25 + RRF"]
    PromptBuilder["PromptBuilder\n上下文与 Prompt"]

    PostgreSQL[("PostgreSQL\nusers / documents / tasks / review_schedule")]
    Qdrant[("Qdrant\nknowledge_chunks\npayload: user_id / doc_id / text")]
    Uploads[("uploads/{user_id}/\nPDF 文件")]
    OpenAI["OpenAI API\nLLM / Embedding"]

    User --> Frontend

    Frontend -- "注册 / 登录 / JWT" --> AuthAPI
    Frontend -- "聊天消息 + JWT" --> ChatAPI
    Frontend -- "PDF 文件 + JWT" --> DocAPI
    Frontend -- "待办 / 计划 / 复习 + JWT" --> TaskAPI

    AuthAPI --> AuthService
    AuthService --> PostgreSQL
    AuthService -- "JWT / user info" --> Frontend

    ChatAPI --> MasterAgent
    MasterAgent --> KnowledgeAgent
    MasterAgent --> PlannerAgent
    MasterAgent -- "general_chat" --> ChatAPI

    KnowledgeAgent --> Retriever
    Retriever --> Qdrant
    Retriever --> PostgreSQL
    Retriever --> PromptBuilder
    PromptBuilder --> OpenAI
    OpenAI -- "流式答案" --> ChatAPI
    ChatAPI -- "SSE: start/content/citations/done" --> Frontend

    DocAPI --> DocumentService
    DocumentService --> Uploads
    DocumentService --> PostgreSQL
    DocumentService --> Parser
    Parser --> Chunker
    Chunker --> Embedding
    Embedding --> OpenAI
    Embedding --> Qdrant
    DocumentService -- "status / total_chunks" --> PostgreSQL

    TaskAPI --> TaskService
    TaskAPI --> ReviewService
    TaskAPI --> PlannerAgent
    PlannerAgent --> OpenAI
    PlannerAgent --> TaskService
    TaskService --> PostgreSQL
    ReviewService --> PostgreSQL
```

---

## 2. 登录注册数据流

```mermaid
sequenceDiagram
    actor U as 用户
    participant FE as Vue 前端
    participant API as Auth Router
    participant SVC as AuthService
    participant SEC as Security
    participant DB as PostgreSQL

    U->>FE: 输入用户名 / 邮箱 / 密码
    FE->>API: POST /api/auth/register 或 /login
    API->>SVC: 校验请求数据
    SVC->>DB: 查询用户 / 写入用户
    SVC->>SEC: 哈希密码或校验密码
    SEC-->>SVC: password_hash 或校验结果
    SVC->>SEC: 生成 JWT
    SEC-->>SVC: access_token
    SVC-->>API: token + user
    API-->>FE: 登录结果
    FE-->>U: 进入主工作台
```

**关键数据**

| 数据 | 来源 | 去向 | 说明 |
| --- | --- | --- | --- |
| `username` / `email` / `password` | 用户输入 | Auth API | 注册或登录凭据 |
| `password_hash` | Security | PostgreSQL | 只保存哈希，不保存明文密码 |
| `access_token` | Security | 前端 | 后续请求放入 `Authorization` |
| `user_id` | PostgreSQL | 后端上下文 | 所有业务查询的数据隔离依据 |

---

## 3. PDF 上传与向量入库数据流

```mermaid
sequenceDiagram
    actor U as 用户
    participant FE as Vue 前端
    participant API as Documents Router
    participant DS as DocumentService
    participant FS as uploads/{user_id}
    participant DB as PostgreSQL
    participant Parser as PDF Parser
    participant Chunker as Chunker
    participant Emb as Embedding
    participant LLM as OpenAI Embedding
    participant VS as Qdrant

    U->>FE: 上传 PDF
    FE->>API: POST /api/documents/upload + JWT + file
    API->>DS: 传入 current_user 和文件
    DS->>FS: 保存 PDF 到用户目录
    DS->>DB: 创建 documents 记录 status=pending
    DS-->>API: task_id
    API-->>FE: 返回 task_id

    DS->>DB: status=processing
    DS->>Parser: 提取 PDF 文本和标题信息
    Parser-->>DS: 页面文本 / 标题候选
    DS->>Chunker: 层级化分块
    Chunker-->>DS: chunks + path + metadata
    DS->>Emb: 批量向量化 chunks
    Emb->>LLM: text-embedding-3-small
    LLM-->>Emb: vectors
    DS->>VS: upsert vectors + payload(user_id, doc_id, path, text)
    DS->>DB: status=done, total_chunks=n

    FE->>API: GET /api/documents/{task_id}/status
    API->>DB: 查询当前用户文档状态
    API-->>FE: processing / done / failed
```

**关键数据**

| 数据 | 来源 | 去向 | 说明 |
| --- | --- | --- | --- |
| PDF 文件 | 前端上传 | `uploads/{user_id}/` | 原始课件文件 |
| `documents` 记录 | DocumentService | PostgreSQL | 文件名、路径、状态、分块数量 |
| chunk metadata | Parser + Chunker | PostgreSQL / Qdrant payload | 包含 `user_id`、`doc_id`、`path`、`text` |
| embedding vector | OpenAI Embedding | Qdrant | 用于语义检索 |
| `user_id` filter | 当前登录用户 | Qdrant 检索/删除 | 多用户隔离硬约束 |

---

## 4. 课件问答 RAG 数据流

```mermaid
sequenceDiagram
    actor U as 用户
    participant FE as ChatPanel
    participant API as Chat Router
    participant M as MasterAgent
    participant K as KnowledgeAgent
    participant R as Retriever
    participant VS as Qdrant
    participant DB as PostgreSQL
    participant PB as PromptBuilder
    participant LLM as OpenAI LLM

    U->>FE: 输入课件问题
    FE->>API: POST /api/chat + JWT + message
    API->>M: message + current_user
    M->>M: 意图识别
    M-->>API: start(intent=knowledge_query)
    M->>K: 路由到知识库智能体
    K->>R: query + user_id
    R->>VS: 向量检索 top-10, filter user_id
    R->>DB: BM25 候选文本 / 文档元数据
    R->>R: RRF 融合排序 top-5
    R-->>K: top chunks + sources
    K->>PB: 组装上下文和 Prompt
    PB-->>K: prompt
    K->>LLM: stream answer
    LLM-->>API: content chunks
    API-->>FE: SSE content
    API-->>FE: SSE citations
    API-->>FE: SSE done
    FE-->>U: 流式展示答案和引用
```

**SSE 数据格式**

```text
data: {"type": "start", "intent": "knowledge_query"}
data: {"type": "content", "text": "最大似然估计是一种..."}
data: {"type": "citations", "sources": ["第2章 > 2.1 最大似然估计"]}
data: {"type": "done"}
```

**关键数据**

| 数据 | 来源 | 去向 | 说明 |
| --- | --- | --- | --- |
| `message` | 用户 | MasterAgent | 用于意图识别 |
| `intent` | MasterAgent | Chat Router / 前端 | 告诉前端当前任务类型 |
| query embedding | Retriever | Qdrant | 语义检索使用 |
| top chunks | Qdrant + BM25 | PromptBuilder | 构造 RAG 上下文 |
| citations | Retriever | 前端 | 展示引用来源 |
| stream content | OpenAI LLM | 前端 | SSE 流式回答 |

---

## 5. 学习计划与待办数据流

```mermaid
sequenceDiagram
    actor U as 用户
    participant FE as ChatPanel / TodoList
    participant API as Chat / Plan / Tasks Router
    participant M as MasterAgent
    participant P as PlannerAgent
    participant LLM as OpenAI LLM
    participant TS as TaskService
    participant RS as ReviewService
    participant DB as PostgreSQL

    U->>FE: 输入“帮我规划高数第3章复习，我有3天”
    FE->>API: POST /api/chat + JWT + message
    API->>M: message + current_user
    M->>M: 识别 plan_create
    M->>P: goal + days + user_id
    P->>LLM: 生成结构化复习计划
    LLM-->>P: plan text + daily tasks
    P->>TS: 创建多个待办
    TS->>DB: 写入 tasks(user_id)
    P-->>API: plan text + created tasks
    API-->>FE: SSE content / done
    FE-->>U: 展示计划并刷新待办列表

    U->>FE: 完成复习并评分
    FE->>API: PUT /api/review/{id}/rate
    API->>RS: score + user_id
    RS->>RS: 计算 SM-2 间隔
    RS->>DB: 更新 next_review_date / interval_days / ease_factor
    API-->>FE: 更新后的复习项
```

**关键数据**

| 数据 | 来源 | 去向 | 说明 |
| --- | --- | --- | --- |
| 学习目标 | 用户输入 | PlannerAgent | 计划生成输入 |
| 计划文本 | OpenAI LLM | 前端 | 展示给用户 |
| daily tasks | PlannerAgent | TaskService | 自动创建待办 |
| `tasks.user_id` | 当前用户 | PostgreSQL | 待办数据隔离 |
| 复习评分 | 用户 | ReviewService | SM-2 更新依据 |
| `next_review_date` | ReviewService | PostgreSQL | 下次复习时间 |

---

## 6. 多用户数据隔离流

```mermaid
flowchart TD
    Token["JWT token"]
    CurrentUser["get_current_user\n解析 user_id"]

    Token --> CurrentUser

    CurrentUser --> DocQuery["documents 查询\nWHERE user_id = current_user.id"]
    CurrentUser --> TaskQuery["tasks 查询\nWHERE user_id = current_user.id"]
    CurrentUser --> ReviewQuery["review_schedule 查询\nWHERE user_id = current_user.id"]
    CurrentUser --> QdrantFilter["Qdrant filter\npayload.user_id = current_user.id"]
    CurrentUser --> UploadPath["文件路径\nuploads/{user_id}/"]

    DocQuery --> PostgreSQL[("PostgreSQL")]
    TaskQuery --> PostgreSQL
    ReviewQuery --> PostgreSQL
    QdrantFilter --> Qdrant[("Qdrant")]
    UploadPath --> FileStore[("Local Files")]
```

**隔离规则**

| 数据位置 | 隔离方式 |
| --- | --- |
| PostgreSQL `documents` | 所有查询、更新、删除必须带 `user_id` |
| PostgreSQL `tasks` | 所有查询、更新、删除必须带 `user_id` |
| PostgreSQL `review_schedule` | 所有查询、更新、删除必须带 `user_id` |
| Qdrant `knowledge_chunks` | payload 必须包含 `user_id`，检索和删除必须 filter |
| 本地 PDF 文件 | 保存到 `uploads/{user_id}/` |
| 前端状态 | 退出登录时清空 token、用户信息、文档、待办、聊天状态 |

---

## 7. 数据流检查清单

| 检查项 | 判断标准 |
| --- | --- |
| 未登录访问业务接口 | 返回 401 |
| 登录后请求业务接口 | 请求头携带 `Authorization: Bearer <token>` |
| 文档上传 | 文件进入 `uploads/{user_id}/`，数据库写入当前用户文档 |
| 向量入库 | Qdrant payload 包含 `user_id` 和 `doc_id` |
| RAG 检索 | Qdrant 检索带 `user_id` filter |
| 待办查询 | 只返回当前用户待办 |
| 复习查询 | 只返回当前用户复习项 |
| 退出登录 | 前端清空 token 和业务状态 |
| SSE 输出 | 事件顺序符合 `start -> content -> citations -> done` |

