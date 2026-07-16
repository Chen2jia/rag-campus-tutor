param(
    [switch] $Local
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")

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
        throw "backend/.env not found. Copy backend/.env.example to backend/.env and configure OPENAI_API_KEY / OPENAI_MODEL first."
    }

    if ($Local) {
        Write-Host "Running LLM live smoke locally..."
        Push-Location "backend"
        try {
            Invoke-Checked "local LLM live smoke" {
                python scripts/llm_live_smoke.py
            }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "Running LLM live smoke inside Docker backend image..."
        Invoke-Checked "docker LLM live smoke" {
            docker compose run --rm --no-deps --volume ./harness/reports:/app/harness/reports backend python scripts/llm_live_smoke.py
        }
    }
}
finally {
    Pop-Location
}
