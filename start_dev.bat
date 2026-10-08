@echo off
title TaSTP - Studio Text-to-Speech Self-Hosted
cd /d "%~dp0"

echo ===================================================
echo   TaSTP - Platform Text-to-Speech Self-Hosted
echo   Kreator Konten & Video Narator AI
echo ===================================================
echo.

if exist "%LOCALAPPDATA%\nodejs\node.exe" (
    set "PATH=%LOCALAPPDATA%\nodejs;%PATH%"
)

echo [INFO] Memulai Backend FastAPI di http://127.0.0.1:8000 ...
if exist "%~dp0backend\.venv\Scripts\python.exe" (
    start "TaSTP Backend" cmd /k "cd /d %~dp0backend && set PYTHONPATH=. && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
) else (
    start "TaSTP Backend" cmd /k "cd /d %~dp0backend && set PYTHONPATH=. && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
)

cd frontend
if not exist "node_modules\" (
    echo [INFO] Menginstal dependensi frontend...
    call npm.cmd install
)

echo [INFO] Menjalankan Frontend Next.js di http://127.0.0.1:3000 ...
start "" "http://127.0.0.1:3000"
call npm.cmd run dev
