@echo off
REM BloodHound AI - Quick Restart Script
REM This helps you get back to the right directory quickly

echo ================================================================
echo BloodHound AI - Environment Setup
echo ================================================================
echo.

cd C:\Users\gordo\Projects\BloodHound-AI

echo Current directory: %CD%
echo.
echo Ready to work! Start Rovo Dev from this directory.
echo.
echo Quick commands:
echo   - Activate venv: .\venv\Scripts\Activate.ps1
echo   - Run tests: pytest tests/
echo.

cmd /k
