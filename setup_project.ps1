$ErrorActionPreference = "Stop"

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path

$BackendSetup = Join-Path `
    $RootPath `
    "finance-ai-backend\setup_backend.ps1"

$FrontendSetup = Join-Path `
    $RootPath `
    "finance-ai-frontend\setup_frontend.ps1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Finance AI Complete Project Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $BackendSetup)) {
    Write-Host "Backend setup script was not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $FrontendSetup)) {
    Write-Host "Frontend setup script was not found." -ForegroundColor Red
    exit 1
}

Write-Host "Setting up backend..." -ForegroundColor Yellow
& $BackendSetup

Write-Host ""
Write-Host "Setting up frontend..." -ForegroundColor Yellow
& $FrontendSetup

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Finance AI setup completed" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Start the project using:" -ForegroundColor Cyan
Write-Host ".\start_project.ps1"
Write-Host ""