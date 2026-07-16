# EduMate

EduMate is a multi-agent campus learning assistant built with Vue 3, FastAPI, PostgreSQL, Qdrant, and OpenAI APIs.

This repository is currently in Phase 2: authentication, user-scoped data models, and harness checks.

## Services

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Backend Docs | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |

## Quick Start

```bash
cp backend/.env.example backend/.env
docker-compose up -d
```

Run migrations:

```bash
docker compose run --rm migrate
```

RAG answers stay in placeholder mode until both values are configured:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=your-model-name
```

## Local Development

```bash
cd backend
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## Harness Checks

```powershell
powershell -ExecutionPolicy Bypass -File harness/scripts/check_skeleton.ps1
powershell -ExecutionPolicy Bypass -File harness/scripts/check_auth_static.ps1
powershell -ExecutionPolicy Bypass -File harness/scripts/check_api_smoke.ps1
```

To run the full local auth flow with Docker:

```powershell
powershell -ExecutionPolicy Bypass -File harness/scripts/run_auth_flow.ps1
```

