$ErrorActionPreference = "Stop"

Write-Host "Starting infrastructure..."
docker compose up -d postgres qdrant

Write-Host "Running migrations..."
docker compose run --rm migrate

Write-Host "Starting backend..."
docker compose up -d backend

Write-Host "Running Auth API smoke harness..."
python harness/runners/api_smoke.py
