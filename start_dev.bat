@echo off
echo Starting RedRob AI Recruiter...
echo.

echo [1/2] Starting FastAPI backend on http://localhost:8000
start "RedRob API" cmd /k "python -m uvicorn api.app:app --reload --port 8000"

timeout /t 2 /nobreak > nul

echo [2/2] Starting React frontend on http://localhost:5173
start "RedRob Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ✓ RedRob AI is starting up!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo.
pause
