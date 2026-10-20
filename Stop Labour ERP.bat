@echo off
echo Stopping Labour ERP...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":3000 .*LISTENING"') do taskkill /F /PID %%p >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do taskkill /F /PID %%p >nul 2>nul
echo Stopped.
timeout /t 2 >nul
