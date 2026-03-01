@echo off
REM AutoHound - Quick Installer (Windows)
REM [ACH] Automated Compromise Hunter

color 0A

echo.
echo ================================================================
echo.
echo    [ACH] AutoHound - Installer
echo    Automated Compromise Hunter
echo.
echo ================================================================
echo.

REM Check for Python
echo [1/5] Checking Python installation...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found! Install Python 3.11+ first.
    echo     Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

REM Create venv
echo.
echo [2/5] Creating virtual environment...
if exist venv (
    echo [!] Virtual environment already exists
) else (
    py -m venv venv
    echo [OK] Virtual environment created
)

REM Upgrade pip
echo.
echo [3/5] Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel --quiet
echo [OK] Pip upgraded

REM Install dependencies
echo.
echo [4/5] Installing AutoHound...
echo     This may take a few minutes...
venv\Scripts\python.exe -m pip install -e . --quiet
if %errorlevel% neq 0 (
    echo [X] Installation failed!
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Setup .env
echo.
echo [5/5] Configuring environment...
if not exist .env (
    copy .env.example .env >nul
    echo [OK] Created .env file
    echo [!] IMPORTANT: Add your Anthropic API key to .env
) else (
    echo [!] .env already exists
)

REM Success
echo.
echo ================================================================
echo.
echo              [+] INSTALLATION COMPLETE
echo.
echo    Next steps:
echo    1. Edit .env and add your Anthropic API key
echo    2. Run: venv\Scripts\activate
echo    3. Run: autohound --help
echo.
echo    [ACH] Ready for deployment
echo.
echo ================================================================
echo.
pause
