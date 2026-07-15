$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    alembic -c alembic.ini upgrade head
}
finally {
    Pop-Location
}
