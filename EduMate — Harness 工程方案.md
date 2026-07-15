# EduMate — Harness 工程方案

> **文档用途**：把 Harness 工程思想应用到 EduMate 项目中，让系统从一开始就具备“可启动、可验证、可回放、可观测、可迭代”的工程能力。  
> **核心目标**：不要只写业务代码，也要为业务代码配套一组稳定的验证外壳，让每次修改都能快速确认是否破坏了登录、多用户隔离、RAG 问答、智能体路由和学习规划。

---

## 1. 什么是 Harness 工程思想

在本项目中，Harness 指的是围绕核心系统建立一套工程外壳：

- **运行 Harness**：一条命令启动完整开发环境。
- **测试 Harness**：一条命令验证核心 API 和业务逻辑。
- **数据 Harness**：用固定样例 PDF、固定用户、固定待办构造可重复数据。
- **RAG Harness**：用标准问题集评估检索结果、引用来源和答案质量。
- **智能体 Harness**：用固定输入验证意图识别、路由和兜底行为。
- **前端 Harness**：用固定用户和模拟数据验证页面主流程。
- **观测 Harness**：记录关键链路日志，方便定位问题。

简单说，Harness 不是替代功能开发，而是给功能开发配一套“仪表盘 + 安全带 + 回放按钮”。

---

## 2. 为什么 EduMate 需要 Harness

EduMate 的复杂度主要来自这些地方：

| 复杂点 | 没有 Harness 的问题 | Harness 要解决什么 |
| --- | --- | --- |
| 多用户登录 | 容易漏掉 `user_id` 过滤 | 自动验证用户 A 看不到用户 B 的数据 |
| PDF 解析 | 不同 PDF 分块质量不稳定 | 固定样例 PDF，持续检查 chunk 结构 |
| RAG 检索 | 改检索逻辑后不知道效果好坏 | 固定问题集，检查 top-k、引用、答案 |
| 智能体路由 | LLM 输出不稳定 | 用样例输入验证 5 类意图和低置信度兜底 |
| SSE 流式输出 | 前端/后端联调容易出错 | 用脚本检查事件顺序和内容格式 |
| 学习计划生成 | LLM 生成格式可能漂移 | 检查是否能生成结构化计划并创建待办 |

---

## 3. Harness 目录设计

建议在项目根目录增加 `harness/`，专门放验证脚本、样例数据和评估集。

```text
edumate/
├── harness/                         # Harness 工程目录，存放验证外壳和样例数据
│   ├── README.md                    # Harness 使用说明和命令索引
│   ├── scripts/                     # 一键运行脚本
│   │   ├── check_backend.ps1        # 后端 API 快速检查
│   │   ├── check_rag.ps1            # RAG 检索与问答检查
│   │   ├── check_agents.ps1         # 智能体意图识别检查
│   │   └── seed_demo_data.ps1       # 写入演示用户、待办、复习数据
│   ├── fixtures/                    # 固定样例数据
│   │   ├── users.json               # 测试用户 A / B
│   │   ├── tasks.json               # 样例待办
│   │   ├── review_points.json       # 样例复习知识点
│   │   └── pdfs/                    # 小型样例 PDF
│   ├── evals/                       # 评估集
│   │   ├── rag_questions.jsonl      # RAG 标准问题与期望引用
│   │   ├── intent_cases.jsonl       # 意图识别样例
│   │   └── planner_cases.jsonl      # 学习计划生成样例
│   ├── runners/                     # Python 检查程序
│   │   ├── api_smoke.py             # 注册、登录、CRUD、鉴权冒烟测试
│   │   ├── user_isolation.py        # 多用户数据隔离测试
│   │   ├── rag_eval.py              # RAG 检索与答案评估
│   │   ├── agent_eval.py            # 智能体路由评估
│   │   └── sse_check.py             # SSE 事件流格式检查
│   └── reports/                     # Harness 运行结果
│       ├── latest.json              # 最近一次运行结果
│       └── history/                 # 历史评估记录
```

---

## 4. Harness 分层设计

| Harness 层级 | 目录 / 文件 | 验证目标 |
| --- | --- | --- |
| 启动 Harness | `docker-compose.yml`、`harness/scripts/check_backend.ps1` | 服务是否能启动，后端是否能访问，数据库和 Qdrant 是否可用。 |
| 认证 Harness | `harness/runners/api_smoke.py` | 注册、登录、`/api/auth/me`、未登录 401 是否正常。 |
| 多用户隔离 Harness | `harness/runners/user_isolation.py` | 用户 A 和用户 B 的文档、待办、复习数据、向量检索是否严格隔离。 |
| 文档处理 Harness | `harness/fixtures/pdfs/`、`harness/runners/rag_eval.py` | PDF 是否能解析、分块、入库，chunk 元数据是否完整。 |
| RAG Harness | `harness/evals/rag_questions.jsonl`、`harness/runners/rag_eval.py` | 检索结果、引用来源、答案是否符合预期。 |
| 智能体 Harness | `harness/evals/intent_cases.jsonl`、`harness/runners/agent_eval.py` | 5 类意图识别、置信度、低置信度澄清是否正常。 |
| Planner Harness | `harness/evals/planner_cases.jsonl` | 计划生成是否结构化，是否能创建待办。 |
| SSE Harness | `harness/runners/sse_check.py` | `/api/chat` 是否按 `start -> content -> citations -> done` 返回。 |
| 前端 Harness | 后续可接 Playwright | 登录、上传、提问、待办等主流程是否可操作。 |
| 报告 Harness | `harness/reports/` | 保存每次运行结果，方便对比迭代前后效果。 |

---

## 5. 最小可用 Harness 命令

第一阶段不需要做复杂平台，只需要几个命令即可：

```powershell
# 1. 检查后端是否可用
powershell -File harness/scripts/check_backend.ps1

# 2. 初始化演示数据
powershell -File harness/scripts/seed_demo_data.ps1

# 3. 检查用户隔离
python harness/runners/user_isolation.py

# 4. 检查 RAG
python harness/runners/rag_eval.py

# 5. 检查智能体
python harness/runners/agent_eval.py
```

后续可以再增加一个总入口：

```powershell
powershell -File harness/scripts/check_all.ps1
```

---

## 6. 样例评估数据格式

### 6.1 意图识别评估集

`harness/evals/intent_cases.jsonl`

```jsonl
{"message":"解释一下最大似然估计","expected_intent":"knowledge_query"}
{"message":"帮我规划高数第3章复习，我有3天时间","expected_intent":"plan_create"}
{"message":"我今天有什么待办","expected_intent":"plan_query"}
{"message":"把高数复习标记为完成","expected_intent":"plan_update"}
{"message":"你好，你能做什么","expected_intent":"general_chat"}
```

### 6.2 RAG 评估集

`harness/evals/rag_questions.jsonl`

```jsonl
{"question":"最大似然估计的核心思想是什么？","expected_source_contains":"最大似然估计","must_answer_contains":["参数","概率"]}
{"question":"课件中提到的梯度下降步骤是什么？","expected_source_contains":"梯度下降","must_answer_contains":["初始化","迭代"]}
```

### 6.3 Planner 评估集

`harness/evals/planner_cases.jsonl`

```jsonl
{"message":"帮我规划高数第3章复习，我有3天时间","expected_days":3,"expected_task_count":3}
{"message":"帮我添加待办：复习线代，明天截止","expected_action":"create_task"}
```

---

## 7. 验收指标

| 指标 | 最低要求 | 理想要求 |
| --- | --- | --- |
| 认证冒烟测试 | 100% 通过 | 100% 通过 |
| 用户隔离测试 | 100% 通过 | 100% 通过 |
| 意图识别准确率 | ≥ 85% | ≥ 95% |
| RAG 引用命中率 | ≥ 70% | ≥ 85% |
| RAG 无结果兜底 | 100% 可触发 | 100% 可触发且提示友好 |
| SSE 事件格式 | 100% 合规 | 100% 合规 |
| 待办 CRUD 测试 | 100% 通过 | 100% 通过 |

---

## 8. 与开发阶段的关系

| 开发阶段 | 应配套的 Harness |
| --- | --- |
| Phase 1：基础设施 | 启动 Harness、健康检查脚本 |
| Phase 2：认证与数据模型 | 认证 Harness、多用户隔离 Harness |
| Phase 3：基础业务 API | API 冒烟 Harness、CRUD 测试 |
| Phase 4：PDF 解析与分块 | PDF fixture、chunk 检查 |
| Phase 5：向量化与检索 | RAG 检索 Harness |
| Phase 6：RAG 问答与 SSE | RAG 问答 Harness、SSE Harness |
| Phase 7：主智能体 | 意图识别 Harness |
| Phase 8：规划智能体 | Planner Harness、SM-2 测试 |
| Phase 9：前端 | 前端主流程 Harness |
| Phase 10：集成测试 | `check_all` 总体验证 |

---

## 9. 开发约定

- 每增加一个关键功能，都要补一个最小 Harness 用例。
- 每修一个 RAG 或智能体问题，都要把对应输入加入 eval 集，避免回归。
- 每次大改检索、Prompt、分块逻辑，都要运行 RAG Harness。
- 每次改认证、数据模型、查询逻辑，都要运行用户隔离 Harness。
- Harness 失败时，优先判断是功能退化、评估集过严，还是测试数据失效。

---

## 10. 项目中的 Harness 优先级

建议优先顺序：

1. **认证 + 用户隔离 Harness**：这是多用户版本的安全底线。
2. **API 冒烟 Harness**：保证基础接口随时可用。
3. **RAG Harness**：保证项目核心亮点可持续迭代。
4. **智能体 Harness**：保证自然语言入口稳定。
5. **SSE Harness**：保证聊天体验不被破坏。
6. **前端 Harness**：等主界面成型后再接入。

