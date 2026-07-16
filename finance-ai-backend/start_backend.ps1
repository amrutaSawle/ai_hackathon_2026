$ErrorActionPreference = "Stop"

$BackendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BackendPath

$PythonExe = Join-Path $BackendPath "venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Virtual environment was not found." -ForegroundColor Red
    Write-Host "Run .\setup_backend.ps1 first." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path ".\.env")) {
    Write-Host ".env was not found." -ForegroundColor Red
    Write-Host "Run .\setup_backend.ps1 first." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting Finance AI backend..." -ForegroundColor Cyan
Write-Host "Swagger: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""

& $PythonExe -m uvicorn main:app `
    --reload `
    --host 127.0.0.1 `
    --port 8000