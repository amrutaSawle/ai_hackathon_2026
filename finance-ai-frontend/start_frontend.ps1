$ErrorActionPreference = "Stop"

$FrontendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $FrontendPath

if (-not (Test-Path ".\node_modules")) {
    Write-Host "Frontend dependencies were not installed." -ForegroundColor Red
    Write-Host "Run .\setup_frontend.ps1 first." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting Finance AI frontend..." -ForegroundColor Cyan
Write-Host "Application: http://localhost:4200" -ForegroundColor Green
Write-Host ""

npx ng serve