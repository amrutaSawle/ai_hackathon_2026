$ErrorActionPreference = "Stop"

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path

$BackendScript = Join-Path `
    $RootPath `
    "finance-ai-backend\start_backend.ps1"

$FrontendScript = Join-Path `
    $RootPath `
    "finance-ai-frontend\start_frontend.ps1"

if (-not (Test-Path $BackendScript)) {
    Write-Host "Backend start script was not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $FrontendScript)) {
    Write-Host "Frontend start script was not found." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting Finance AI backend and frontend..." -ForegroundColor Cyan
Write-Host ""

Start-Process powershell `
    -ArgumentList `
    "-NoExit", `
    "-ExecutionPolicy", `
    "Bypass", `
    "-File", `
    "`"$BackendScript`""

Start-Sleep -Seconds 3

Start-Process powershell `
    -ArgumentList `
    "-NoExit", `
    "-ExecutionPolicy", `
    "Bypass", `
    "-File", `
    "`"$FrontendScript`""

Write-Host "Backend starting at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend starting at http://localhost:4200" -ForegroundColor Green
Write-Host "Swagger available at http://127.0.0.1:8000/docs" -ForegroundColor Green