# EduMate

EduMate is a multi-agent campus learning assistant built with Vue 3, FastAPI, PostgreSQL, Qdrant, and OpenAI APIs.

This repository is currently in Phase 1: project skeleton and local infrastructure.

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

