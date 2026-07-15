$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    uvicorn app.main:app --reload
}
finally {
    Pop-Location
}
