@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv was not found.
    echo Run setup.bat first.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] .env was not found.
    echo Run setup.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m app.main
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] The bot stopped with an error.
    echo Keep the error above and send it for debugging.
    pause
    exit /b %EXIT_CODE%
)
