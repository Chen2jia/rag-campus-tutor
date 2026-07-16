$ErrorActionPreference = "Stop"

python harness/runners/rag_eval.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
