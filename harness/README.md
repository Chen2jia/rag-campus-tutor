# EduMate Harness

This directory contains repeatable checks, fixtures, eval cases, and reports for EduMate.

## Available Checks

```powershell
# Check the Phase 1 project skeleton.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_skeleton.ps1

# Check that auth files, models, and migrations exist.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_auth_static.ps1

# Run real auth API smoke checks against a running backend.
powershell -ExecutionPolicy Bypass -File harness/scripts/check_api_smoke.ps1
```

## Auth API Smoke

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
