$ErrorActionPreference = "Stop"

python harness/runners/e2e_demo_flow.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
