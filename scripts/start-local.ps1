# LitScope Local — native start (no Docker)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== LitScope native boot ==" -ForegroundColor Cyan

# 1) Backend deps
$backend = Join-Path $root "backend"
Set-Location $backend
if (-not (Test-Path ".venv")) {
  Write-Host "Creating backend venv..."
  python -m venv .venv
}
$py = Join-Path $backend ".venv\Scripts\python.exe"
& $py -m pip install -q -r requirements.txt

# 2) Frontend deps
$frontend = Join-Path $root "frontend"
Set-Location $frontend
if (-not (Test-Path "node_modules")) {
  Write-Host "Installing frontend packages..."
  npm install
}

# 3) Start backend (SQLite + in-process scheduler by default)
$env:DATABASE_URL = $env:DATABASE_URL
if (-not $env:DATABASE_URL) {
  $dbPath = Join-Path $backend "litscope.db"
  $env:DATABASE_URL = "sqlite+aiosqlite:///$($dbPath -replace '\\','/')"
}
$env:ENABLE_SCHEDULER = "true"
$env:REFRESH_MODE = "inline"
$env:CORS_ORIGINS = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"

Write-Host "Starting API on :8000 ..."
Start-Process -FilePath $py -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory $backend

Write-Host "Starting frontend on :3000 ..."
Start-Process -FilePath "npm" -ArgumentList "run","dev" -WorkingDirectory $frontend

Write-Host ""
Write-Host "API  http://127.0.0.1:8000/api/health" -ForegroundColor Green
Write-Host "UI   http://localhost:3000" -ForegroundColor Green
Write-Host "Docs http://127.0.0.1:8000/docs" -ForegroundColor Green
