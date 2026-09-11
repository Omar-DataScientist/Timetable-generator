# ============================================================
#  TimetableGen — Project Startup Script (PowerShell)
#  Usage: .\execute.ps1
#         Run from:  d:\Antigravity\Timetable_Generator\
# ============================================================

$Host.UI.RawUI.WindowTitle = "TimetableGen Startup"
$ProjectRoot = $PSScriptRoot   # directory where this script lives
$BackendDir  = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$Uvicorn     = Join-Path $BackendDir  "venv\Scripts\uvicorn.exe"

Write-Host ""
Write-Host "  =====================================================" -ForegroundColor Cyan
Write-Host "   TimetableGen | OR-Tools CP-SAT Scheduler" -ForegroundColor Cyan
Write-Host "  =====================================================" -ForegroundColor Cyan
Write-Host ""

# ── Pre-flight checks ─────────────────────────────────────────────────────
if (-not (Test-Path $Uvicorn)) {
    Write-Host "  [ERROR] Virtual environment not found at:" -ForegroundColor Red
    Write-Host "          $BackendDir\venv" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Fix: cd backend; python -m venv venv; venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "  Press Enter to exit"
    exit 1
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "  [ERROR] node_modules not found. Installing now..." -ForegroundColor Yellow
    Set-Location $FrontendDir
    npm install
    Set-Location $ProjectRoot
}

# ── Start Backend ─────────────────────────────────────────────────────────
Write-Host "  [1/2] Starting FastAPI backend..." -ForegroundColor Green
Write-Host "        URL:      http://localhost:8000" -ForegroundColor DarkGray
Write-Host "        API Docs: http://localhost:8000/docs" -ForegroundColor DarkGray
Write-Host ""

$BackendCmd = "cd '$BackendDir'; venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd -WindowStyle Normal

# Give the backend 3 seconds to boot
Start-Sleep -Seconds 3

# ── Start Frontend ────────────────────────────────────────────────────────
Write-Host "  [2/2] Starting React frontend..." -ForegroundColor Green
Write-Host "        URL: http://localhost:5173" -ForegroundColor DarkGray
Write-Host ""

$FrontendCmd = "cd '$FrontendDir'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCmd -WindowStyle Normal

# Give Vite 2 seconds to bind
Start-Sleep -Seconds 2

# ── Open browser ──────────────────────────────────────────────────────────
Write-Host "  Opening browser at http://localhost:5173 ..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "  =====================================================" -ForegroundColor Cyan
Write-Host "   Both servers are running in separate windows." -ForegroundColor Cyan
Write-Host "   Close those windows to stop the application." -ForegroundColor Cyan
Write-Host "  =====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend  : http://localhost:5173" -ForegroundColor White
Write-Host "  Backend   : http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs  : http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Read-Host "  Press Enter to close this window"
