$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Finance AI Backend Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$BackendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BackendPath

function Test-CommandExists {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# ---------------------------------------------------------
# 1. Verify Python
# ---------------------------------------------------------

if (-not (Test-CommandExists "python")) {
    Write-Host "Python was not found." -ForegroundColor Red
    Write-Host "Install Python 3.13 and enable Add Python to PATH."
    exit 1
}

Write-Host "Python detected:" -ForegroundColor Green
python --version

# ---------------------------------------------------------
# 2. Create virtual environment
# ---------------------------------------------------------

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host ""
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}
else {
    Write-Host ""
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

$PythonExe = Join-Path $BackendPath "venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Virtual environment creation failed." -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------
# 3. Install dependencies
# ---------------------------------------------------------

Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip

if (-not (Test-Path ".\requirements.txt")) {
    Write-Host "requirements.txt was not found." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
& $PythonExe -m pip install -r requirements.txt

# ---------------------------------------------------------
# 4. Create .env from example
# ---------------------------------------------------------

if (-not (Test-Path ".\.env")) {
    if (-not (Test-Path ".\.env.example")) {
        Write-Host ".env.example was not found." -ForegroundColor Red
        exit 1
    }

    Copy-Item ".\.env.example" ".\.env"

    Write-Host ""
    Write-Host ".env created from .env.example." -ForegroundColor Yellow
    Write-Host "Update the PostgreSQL password in:" -ForegroundColor Yellow
    Write-Host "$BackendPath\.env" -ForegroundColor Cyan

    notepad ".\.env"

    Write-Host ""
    Read-Host "After saving .env, press Enter to continue"
}
else {
    Write-Host ""
    Write-Host ".env already exists." -ForegroundColor Green
}

# ---------------------------------------------------------
# 5. Verify PostgreSQL connectivity
# ---------------------------------------------------------

Write-Host ""
Write-Host "Testing database connection..." -ForegroundColor Yellow

$DatabaseTest = @'
from sqlalchemy import text
from app.db.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user")
        ).fetchone()

        print(
            f"Database connection successful: "
            f"database={result[0]}, user={result[1]}"
        )
except Exception as error:
    print(f"Database connection failed: {error}")
    raise
'@

$DatabaseTest | & $PythonExe -

# ---------------------------------------------------------
# 6. Run Alembic migrations
# ---------------------------------------------------------

Write-Host ""
Write-Host "Applying database migrations..." -ForegroundColor Yellow
& $PythonExe -m alembic upgrade head

# ---------------------------------------------------------
# 7. Seed database
# ---------------------------------------------------------

Write-Host ""
Write-Host "Seeding database..." -ForegroundColor Yellow

if (Test-Path ".\seeds\seed_all.py") {
    & $PythonExe -m seeds.seed_all
}
elseif (Test-Path ".\seed_all.py") {
    & $PythonExe ".\seed_all.py"
}
else {
    Write-Host "Seed script was not found. Skipping seed step." -ForegroundColor Yellow
}

# ---------------------------------------------------------
# 8. Verify FastAPI application imports
# ---------------------------------------------------------

Write-Host ""
Write-Host "Verifying FastAPI application..." -ForegroundColor Yellow
& $PythonExe -c "from main import app; print('FastAPI application imported successfully.')"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Backend setup completed successfully" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Run the backend using:" -ForegroundColor Cyan
Write-Host ".\start_backend.ps1"
Write-Host ""