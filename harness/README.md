# EduMate Harness

This directory contains repeatable checks, fixtures, eval cases, and reports for EduMate.

## Available Checks

```powershell
# Check the Phase 1 project skeleton.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_skeleton.ps1

# Check that auth files, models, and migrations exist.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_auth_static.ps1

# Check that document API files and user isolation filters exist.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_documents_static.ps1

# Check that task API files and user isolation filters exist.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_tasks_static.ps1

# Check that review API files, due-date filters, and SM-2 logic exist.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_review_static.ps1

# Check that plan generation and PlannerAgent placeholder flow exist.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_plan_static.ps1

# Run all Phase 1-3 static harness checks.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_phase3_static.ps1

# Check the Phase 4 PDF parser module.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_parser_static.ps1

# Check formula normalization and OCR confidence gate modules.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_formula_static.ps1

# Check chunk generation and formula-preserving metadata.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_chunker_static.ps1

# Check upload-to-parse-to-chunks document processing integration.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_document_processing_static.ps1

# Check persisted document chunk model, migration, and metadata storage.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_document_chunks_static.ps1

# Check user-scoped keyword search over persisted document chunks.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_document_search_static.ps1

# Run real auth API smoke checks against a running backend.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_api_smoke.ps1

# Start infrastructure, run migrations, start backend, then run Auth API smoke.
powershell -ExecutionPolicy Bypass -File harness/scripts/run_auth_flow.ps1
```

## Auth API Smoke

## Phase 3 Static Harness

`check_phase3_static.ps1` is the recommended quick gate before committing backend foundation changes. It runs:

- skeleton check
- auth static check
- documents static check
- tasks static check
- review static check
- plan static check

It does not require Docker, a database, or network access.

`check_api_smoke.ps1` expects the backend to be running. By default it calls:

```text
http://localhost:8000
```

Override the target with:

```powershell
$env:EDUMATE_BASE_URL="http://localhost:8000"
powershell -ExecutionPolicy Bypass -File harness/scripts/check_api_smoke.ps1
```

It verifies:

- unauthenticated `/api/auth/me` returns `401`
- `POST /api/auth/register` returns a token and user
- `POST /api/auth/login` returns a token
- authenticated `/api/auth/me` returns the registered user

The latest result is written to:

```text
harness/reports/latest_auth_smoke.json
```

## Local Infrastructure

```powershell
# Start only PostgreSQL and Qdrant.
powershell -ExecutionPolicy Bypass -File harness/scripts/start_infra.ps1

# Run backend migrations locally from the backend directory.
powershell -ExecutionPolicy Bypass -File backend/scripts/migrate.ps1

# Run the backend locally.
powershell -ExecutionPolicy Bypass -File backend/scripts/run_dev.ps1
```
