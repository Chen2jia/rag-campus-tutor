param(
    [switch] $SkipDocker,
    [int] $TimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$BackendBaseUrl = if ($env:EDUMATE_BASE_URL) { $env:EDUMATE_BASE_URL.TrimEnd("/") } else { "http://localhost:8000" }
$RequiredPaths = @(
    "/api/health",
    "/api/auth/register",
    "/api/auth/login",
    "/api/documents/upload",
    "/api/rag/ask",
    "/api/chat",
    "/api/plan/generate",
    "/api/llm/status"
)

function Test-EdumateBackend {
    param([string] $BaseUrl)

    try {
        $openapi = Invoke-RestMethod -Uri "$BaseUrl/openapi.json" -Method Get -TimeoutSec 3
    }
    catch {
        return $false
    }

    foreach ($path in $RequiredPaths) {
        if (-not $openapi.paths.PSObject.Properties.Name.Contains($path)) {
            return $false
        }
    }
    return $true
}

function Wait-EdumateBackend {
    param(
        [string] $BaseUrl,
        [int] $TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-EdumateBackend -BaseUrl $BaseUrl) {
            Write-Host "EduMate backend is ready at $BaseUrl"
            return
        }
        Start-Sleep -Seconds 2
    }

    throw "EduMate backend was not ready at $BaseUrl within $TimeoutSeconds seconds. Check port conflicts or set EDUMATE_BASE_URL."
}

function Invoke-Checked {
    param(
        [string] $Label,
        [scriptblock] $Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Push-Location $Root
try {
    if (-not (Test-Path "backend/.env")) {
        Write-Host "backend/.env not found; copying backend/.env.example"
        Copy-Item "backend/.env.example" "backend/.env"
    }

    if (-not $SkipDocker) {
        Write-Host "Starting PostgreSQL and Qdrant..."
        Invoke-Checked "docker compose up postgres qdrant" {
            docker compose up -d postgres qdrant
        }

        Write-Host "Running migrations..."
        Invoke-Checked "docker compose run migrate" {
            docker compose run --rm migrate
        }

        if ($BackendBaseUrl -eq "http://localhost:8000") {
            Write-Host "Starting EduMate backend..."
            Invoke-Checked "docker compose up backend" {
                docker compose up -d backend
            }
        }
        else {
            Write-Host "Using external EduMate backend: $BackendBaseUrl"
        }
    }
    else {
        Write-Host "Skipping Docker startup. Expecting EduMate backend at $BackendBaseUrl"
    }

    Wait-EdumateBackend -BaseUrl $BackendBaseUrl -TimeoutSeconds $TimeoutSeconds

    Write-Host "Checking LLM configuration status..."
    Invoke-Checked "LLM config harness" {
        python harness/runners/llm_config_check.py
    }

    Write-Host "Running E2E demo flow..."
    Invoke-Checked "E2E demo flow harness" {
        python harness/runners/e2e_demo_flow.py
    }
}
finally {
    Pop-Location
}
