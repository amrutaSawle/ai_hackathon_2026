$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Finance AI Frontend Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$FrontendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $FrontendPath

function Test-CommandExists {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "node")) {
    Write-Host "Node.js was not found." -ForegroundColor Red
    Write-Host "Install the Node.js LTS version."
    exit 1
}

if (-not (Test-CommandExists "npm")) {
    Write-Host "npm was not found." -ForegroundColor Red
    exit 1
}

Write-Host "Node.js detected:" -ForegroundColor Green
node --version

Write-Host "npm detected:" -ForegroundColor Green
npm --version

if (-not (Test-Path ".\package.json")) {
    Write-Host "package.json was not found." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
npm install

Write-Host ""
Write-Host "Building Angular application..." -ForegroundColor Yellow
npm run build

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Frontend setup completed successfully" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Run the frontend using:" -ForegroundColor Cyan
Write-Host ".\start_frontend.ps1"
Write-Host ""