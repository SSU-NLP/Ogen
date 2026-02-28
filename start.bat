@echo off
cd /d "%~dp0"

REM Kill existing processes on ports 8000 and 5173
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

npx concurrently ^
  -n "BACKEND,FRONTEND" ^
  -c "blue,green" ^
  --kill-others ^
  "cd apps/server && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000" ^
  "cd apps/front && pnpm dev"
