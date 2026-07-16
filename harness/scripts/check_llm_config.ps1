$ErrorActionPreference = "Stop"

python harness/runners/llm_config_check.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
