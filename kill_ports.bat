@echo off
setlocal
echo ===================================================
echo [CLEANUP] Stopping processes on ports 8000 and 1420
echo ===================================================

:: Check for Port 8000 (Backend)
echo Checking port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Found process %%a using port 8000. Killing...
    taskkill /F /PID %%a
)

:: Check for Port 1420 (Frontend)
echo Checking port 1420...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :1420 ^| findstr LISTENING') do (
    echo Found process %%a using port 1420. Killing...
    taskkill /F /PID %%a
)

echo.
echo Cleanup complete. You can now restart your project.
echo ===================================================
pause
