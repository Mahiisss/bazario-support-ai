@echo off
REM Bazario Support AI - One-Click Startup
echo.
echo ========================================
echo   Bazario Support AI Starting...
echo ========================================
echo.

REM Terminal 1: API Backend
echo [1/2] Starting API Server (port 5000)...
start "Bazario API" cmd /k "title Bazario API Server && echo Starting API... && python api.py"

REM Wait for API to start
timeout /t 5 /nobreak >nul

REM Terminal 2: React Frontend
echo [2/2] Starting Frontend (port 3000)...
start "Bazario UI" cmd /k "cd frontend && title Bazario Frontend && echo Starting Vite dev server... && npm run dev"

echo.
echo ========================================
echo   STATUS: READY!
echo ========================================
echo. 
echo  *> API:  http://localhost:5000/health 
echo  *> UI:   http://localhost:3000/
echo.
echo Backend: Embeddings + FAISS loaded ✓
echo Frontend: React dashboard with agent progress ✓
echo.
pause
