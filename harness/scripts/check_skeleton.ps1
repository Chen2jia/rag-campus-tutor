$ErrorActionPreference = "Stop"

$requiredPaths = @(
    "docker-compose.yml",
    "backend/app/main.py",
    "backend/app/core/config.py",
    "backend/app/routers/health.py",
    "frontend/package.json",
    "frontend/src/main.ts",
    "frontend/src/App.vue",
    "harness/README.md"
)

$missing = @()
foreach ($path in $requiredPaths) {
    if (-not (Test-Path $path)) {
        $missing += $path
    }
}

if ($missing.Count -gt 0) {
    Write-Error "Missing required paths: $($missing -join ', ')"
}

Write-Host "Skeleton check passed."

