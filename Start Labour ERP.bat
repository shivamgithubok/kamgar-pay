@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or not on PATH.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js / npm is not installed or not on PATH.
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo Installing frontend packages. This is only needed the first time.
  pushd frontend
  call npm install
  popd
)

start "Labour ERP API" cmd /k "cd /d "%~dp0backend" && python -m uvicorn src.main:app --reload --port 8000"
start "Labour ERP Web" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Waiting for the site to start...
timeout /t 8 /nobreak >nul
start "" "http://localhost:3000"

echo.
echo Labour ERP is starting.
echo   Web: http://localhost:3000
echo   API: http://localhost:8000
echo Close the two black windows to stop the app.
echo.
pause
