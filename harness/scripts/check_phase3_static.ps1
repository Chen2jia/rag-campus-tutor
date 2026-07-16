$ErrorActionPreference = "Stop"

$checks = @(
    @{ Name = "Skeleton"; Script = "harness/scripts/check_skeleton.ps1" },
    @{ Name = "Auth"; Script = "harness/scripts/check_auth_static.ps1" },
    @{ Name = "Documents"; Script = "harness/scripts/check_documents_static.ps1" },
    @{ Name = "Tasks"; Script = "harness/scripts/check_tasks_static.ps1" },
    @{ Name = "Review"; Script = "harness/scripts/check_review_static.ps1" },
    @{ Name = "Plan"; Script = "harness/scripts/check_plan_static.ps1" }
)

foreach ($check in $checks) {
    Write-Host "Running $($check.Name) static check..."
    powershell -ExecutionPolicy Bypass -File $check.Script
}

Write-Host "Phase 3 static harness passed."
