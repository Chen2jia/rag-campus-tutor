# EduMate — 当前落地状态与运行手册

## 版本状态

当前版本定位为 `v0.1.0-demo`，目标是先完成一个可本地启动、可演示、可继续迭代的基础版本。

已验证通过：

| 项目 | 状态 |
| --- | --- |
| DeepSeek / OpenAI-compatible LLM smoke | passed |
| Docker E2E flow | passed |
| 注册 / 登录 / JWT | passed |
| PDF 上传与状态查询 | passed |
| 用户数据隔离 | passed |
| RAG ask 接口 | passed |
| SSE chat | passed |
| 学习计划生成 | passed |
| 任务隔离 | passed |

暂不继续推进：

| 项目 | 说明 |
| --- | --- |
| RAG fallback 严格阈值 | 已尝试，但会压低正常召回；当前跳过，后续作为 RAG 质量评估专项处理 |
| 复杂 OCR / 多模态图表识别 | 不属于当前 demo 范围 |
| 聊天历史持久化 | 后续迭代 |
| 前端 Playwright 真实交互测试 | 后续迭代 |

## 环境配置

复制环境变量：

```bash
cp backend/.env.example backend/.env
```

DeepSeek 兼容配置示例：

```env
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

说明：

- 不要提交真实 `.env`。
- `OPENAI_BASE_URL` 为空时，也可以接 OpenAI 官方接口。
- 当前 LLM status 和 smoke 报告不会输出 API key。

## 启动服务

```bash
docker compose up -d postgres qdrant
docker compose run --rm migrate
docker compose up -d backend
```

可选启动前端：

```bash
docker compose up -d frontend
```

默认访问地址：

| 服务 | 地址 |
| --- | --- |
| Backend API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |
| Qdrant Dashboard | http://localhost:6333/dashboard |

## 验证命令

LLM live smoke：

```bash
powershell -ExecutionPolicy Bypass -File harness\scripts\run_llm_live_smoke.ps1
```

完整 E2E：

```bash
powershell -ExecutionPolicy Bypass -File harness\scripts\run_e2e_flow.ps1
```

前端静态检查：

```bash
powershell -ExecutionPolicy Bypass -File harness\scripts\check_frontend_rag_static.ps1
powershell -ExecutionPolicy Bypass -File harness\scripts\check_frontend_chat_static.ps1
```

后端静态测试：

```bash
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q backend\tests
```

## 当前验收口径

本阶段以完整 E2E 通过作为主验收口径。RAG eval 仍保留为质量观察工具，但不作为当前 demo 阻塞项。

原因：

- 当前 RAG eval fixture 很小，容易受单个测试 PDF 和检索阈值影响。
- 强行调高 fallback 阈值会降低正常知识召回。
- 后续应扩充 eval 数据集，再做更稳的相关性策略。

## 下一轮建议

1. RAG eval 扩充：增加更多固定 PDF、问题集和期望来源。
2. 前端体验打磨：上传失败、空状态、加载状态、移动端布局。
3. 部署准备：补充云服务器部署说明、生产环境变量、服务健康检查。
