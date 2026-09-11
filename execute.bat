@echo off
title Timetable Generator — Startup
color 0B

echo.
echo  =====================================================
echo    TimetableGen ^| OR-Tools CP-SAT Scheduler
echo  =====================================================
echo.

:: ── Step 1: Check we are in the right directory ──────────────────────────
if not exist "backend\venv\Scripts\uvicorn.exe" (
    echo  [ERROR] Cannot find backend\venv.
    echo  Make sure you run this file from:
    echo    d:\Antigravity\Timetable_Generator\
    echo.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo  [ERROR] Cannot find frontend\node_modules.
    echo  Run:  cd frontend ^&^& npm install
    echo.
    pause
    exit /b 1
)

:: ── Step 2: Start FastAPI Backend ────────────────────────────────────────
echo  [1/2] Starting FastAPI backend on http://localhost:8000 ...
echo        API Docs: http://localhost:8000/docs
echo.
start "TimetableGen Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait 3 seconds for the backend to initialise
timeout /t 3 /nobreak >nul

:: ── Step 3: Start Vite Frontend ──────────────────────────────────────────
echo  [2/2] Starting React frontend on http://localhost:5173 ...
echo.
start "TimetableGen Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait 2 seconds then open the browser
timeout /t 2 /nobreak >nul

:: ── Step 4: Open browser ─────────────────────────────────────────────────
echo  Opening browser ...
start "" "http://localhost:5173"

echo.
echo  =====================================================
echo    Both servers are running in separate windows.
echo    Close those windows to stop the application.
echo  =====================================================
echo.
echo  Useful links:
echo    Frontend  : http://localhost:5173
echo    Backend   : http://localhost:8000
echo    API Docs  : http://localhost:8000/docs
echo.
pause
