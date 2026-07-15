# 📚 EduMate — 多智能体校园学习助手

> **面向大学生的 AI 学习工作台**：支持轻量登录注册、个人课件知识库、RAG 智能问答、学习计划生成与间隔重复复习。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-向量数据库-orange.svg)](https://qdrant.tech/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-支持-2496ED.svg)](https://www.docker.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991.svg)](https://openai.com/)

---

## 项目简介

**EduMate** 是一款面向在校大学生和自学者的 AI 学习助手 Web 应用。它把“课件知识检索”和“学习计划执行”放在同一个工作台中：用户登录后可以上传自己的 PDF 课件，围绕课件内容提问，并让系统生成复习计划、管理待办和安排间隔重复。

项目采用 **轻量多用户设计**：支持注册登录和 JWT 会话，所有文档、向量、待办、复习数据都按用户隔离；但不引入复杂权限、组织空间、管理员后台等额外系统，保持个人学习助手的清晰边界。

---

## 核心能力

| 模块 | 核心职责 | 关键特性 |
| --- | --- | --- |
| 用户系统 | 轻量账号与数据隔离 | 注册、登录、JWT、密码哈希、按 `user_id` 隔离数据 |
| 主智能体 | 意图识别与任务分发 | 识别知识问答、计划创建、待办查询、计划更新、日常闲聊 |
| 知识库智能体 | 课件 RAG 问答 | PDF 上传、层级化分块、向量检索、BM25、RRF、引用来源 |
| 规划智能体 | 学习任务与复习管理 | 待办 CRUD、计划生成、SM-2 简化版间隔重复 |
| 前端工作台 | 学习交互入口 | 登录页、聊天界面、文档管理、待办视图、流式输出 |
| Harness 工程 | 可验证工程外壳 | 启动检查、API 冒烟、多用户隔离、RAG/智能体评估 |

---

## 系统架构

```mermaid
graph TD
    User[用户] --> Frontend[Vue 3 前端]
    Frontend -- JWT / HTTP / SSE --> Backend[FastAPI 后端]

    subgraph Backend [后端服务]
        Auth[认证模块<br>注册 登录 JWT]
        Master[主智能体<br>意图识别与路由]
        Knowledge[知识库智能体<br>RAG 问答引擎]
        Planner[规划智能体<br>待办与复习计划]
    end

    Auth --> PostgreSQL[(PostgreSQL)]
    Master --> Knowledge
    Master --> Planner

    Knowledge -- user_id filter --> Qdrant[(Qdrant 向量库)]
    Knowledge --> PostgreSQL
    Knowledge --> OpenAI[OpenAI API<br>Embedding + LLM]

    Planner --> PostgreSQL
```

---

## 技术栈

| 层级 | 技术选型 | 作用 |
| --- | --- | --- |
| 前端 | Vue 3 + Vite | 构建桌面端学习工作台 |
| 后端 | FastAPI | 提供异步 API 与 SSE 流式输出 |
| 认证 | JWT + bcrypt/passlib | 轻量登录注册与密码保护 |
| 关系数据库 | PostgreSQL | 存储用户、文档、待办、复习计划 |
| 向量数据库 | Qdrant | 存储文档向量并支持过滤检索 |
| AI 模型 | OpenAI API | 意图识别、RAG 问答、Embedding |
| PDF 解析 | PyMuPDF | 提取 PDF 文本和标题特征 |
| 部署 | Docker Compose | 本地一键启动 |

---

## 当前版本范围

### 必做

- 用户注册、登录、退出、当前用户信息
- 多用户数据隔离
- PDF 上传、解析、分块、向量化入库
- 基于当前用户课件的 RAG 问答
- SSE 流式聊天
- 待办管理和计划生成
- SM-2 简化版复习调度
- Docker Compose 本地启动

### 不做

- 管理员后台、角色权限、组织空间
- 第三方登录、邮箱验证、找回密码流程
- OCR、手写识别、复杂公式识别
- 聊天历史持久化
- 移动端深度适配
- 语音输入/输出
- 付费和用量计费

---

## 快速开始

### 前置条件

- 安装 Docker 和 Docker Compose
- 准备 OpenAI API Key

### 配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`：

```env
OPENAI_API_KEY=sk-xxx
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/edumate
QDRANT_URL=http://qdrant:6333
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### 启动服务

```bash
docker-compose up -d
```

| 服务 | 地址 |
| --- | --- |
| 前端界面 | http://localhost:5173 |
| 后端 API 文档 | http://localhost:8000/docs |
| Qdrant 控制台 | http://localhost:6333/dashboard |

---

## 项目结构

```text
edumate/
├── backend/                         # FastAPI 后端服务，负责认证、业务 API、智能体和 RAG
│   ├── app/                         # 后端应用主包
│   │   ├── main.py                  # 应用入口，注册路由、中间件、健康检查
│   │   ├── db.py                    # PostgreSQL 连接、Session、SQLAlchemy Base
│   │   ├── core/                    # 基础设施层：配置、安全、鉴权依赖
│   │   │   ├── config.py            # 环境变量配置
│   │   │   ├── security.py          # 密码哈希、JWT 生成与解析
│   │   │   └── deps.py              # get_current_user、get_db 等依赖
│   │   ├── models/                  # SQLAlchemy 表模型
│   │   ├── schemas/                 # Pydantic 请求和响应结构
│   │   ├── routers/                 # API 路由：auth、chat、documents、tasks、plan、review
│   │   ├── services/                # 业务服务：认证、文档、待办、复习、LLM 调用
│   │   ├── agents/                  # 三个智能体：Master、Knowledge、Planner
│   │   └── rag/                     # RAG 模块：解析、分块、Embedding、Qdrant、BM25、RRF
│   ├── alembic/                     # 数据库迁移脚本
│   ├── uploads/                     # 上传文件目录，按 user_id 分目录保存
│   ├── tests/                       # 后端测试
│   ├── requirements.txt             # Python 依赖
│   └── .env.example                 # 环境变量示例
├── frontend/                        # Vue 3 前端应用
│   ├── src/
│   │   ├── main.ts                  # 前端入口
│   │   ├── App.vue                  # 根组件
│   │   ├── router/                  # 页面路由和登录守卫
│   │   ├── api/                     # API 封装，统一处理 JWT 和错误
│   │   ├── stores/                  # 用户状态、文档状态、待办状态
│   │   ├── views/                   # Login、Register、Home 页面
│   │   └── components/              # ChatPanel、DocumentManager、TodoList 等组件
│   └── package.json                 # 前端依赖与脚本
├── docker-compose.yml               # PostgreSQL、Qdrant、后端、前端的一键编排
├── harness/                         # 启动检查、样例数据、RAG/智能体评估与报告
├── README.md                        # 项目启动与演示说明
└── docs/                            # 可选：后续设计文档与接口说明
```

---

## 项目亮点

1. **完整 RAG 链路**：PDF 解析、层级化分块、Embedding、Qdrant、BM25、RRF、引用来源。
2. **多智能体协作**：主智能体负责理解和调度，知识库智能体负责课件问答，规划智能体负责学习任务。
3. **轻量多用户设计**：支持真实用户注册登录，数据按 `user_id` 严格隔离，但不引入过重权限系统。
4. **学习场景闭环**：从“上传课件并提问”到“生成计划并复习”，覆盖学习前、中、后的关键动作。
5. **工程化完整度**：前后端分离、Docker Compose、SSE 流式交互、环境变量配置、模块化后端结构。
6. **Harness 工程思想**：用固定样例、检查脚本和评估集持续验证登录、多用户隔离、RAG、智能体和 SSE 主链路。

---

## 推荐开发顺序

1. 项目初始化与 Docker 基础设施
2. 用户注册登录、JWT 和数据模型
3. 文档、待办、复习池基础 API
4. PDF 解析与分块
5. Embedding、Qdrant 和混合检索
6. RAG 问答与 SSE
7. 主智能体路由
8. 规划智能体与 SM-2
9. 前端完整工作台
10. 集成测试与 README 完善

详细任务见：[EduMate — 项目实施计划（Plan）.md](./EduMate%20%E2%80%94%20%E9%A1%B9%E7%9B%AE%E5%AE%9E%E6%96%BD%E8%AE%A1%E5%88%92%EF%BC%88Plan%EF%BC%89.md)

---

## 许可证

MIT © 2026 EduMate
