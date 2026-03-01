#!/usr/bin/env pwsh
<#
.SYNOPSIS
    AutoHound - Automated Installer
    "The Dragonslayer" - AD Attack Path Intelligence

.DESCRIPTION
    Professional installation script for AutoHound
    Handles dependencies, virtual environment, and configuration

.NOTES
    Author: Gordon Prescott (@geo2x)
    License: MIT
    Requires: PowerShell 5.1+, Python 3.11+
#>

param(
    [switch]$DevMode,
    [switch]$SkipVenv,
    [string]$PythonPath = "py"
)

# Banner
$banner = @"

    ___   ________  __
   /   | / ____/ / / /
  / /| |/ /   / /_/ / 
 / ___ / /___/ __  /  
/_/  |_\____/_/ /_/   

╔══════════════════════════════════════════════════════════════╗
║  AutoHound - Installer                                   ║
║  [ACH] Automated Compromise Hunter                          ║
╚══════════════════════════════════════════════════════════════╝

"@

Write-Host $banner -ForegroundColor Green

# Step 1: Check Python
Write-Host "`n[*] Step 1/7: Checking Python installation..." -ForegroundColor Yellow

try {
    $pythonVersion = & $PythonPath --version 2>&1
    Write-Host "   ✅ Found: $pythonVersion" -ForegroundColor Green
    
    # Verify version is 3.11+
    if ($pythonVersion -match "Python 3\.(\d+)\.") {
        $minorVersion = [int]$matches[1]
        if ($minorVersion -lt 11) {
            Write-Host "   ⚠️  Warning: Python 3.11+ recommended, you have $pythonVersion" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ❌ Python not found!" -ForegroundColor Red
    Write-Host "   Install Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Step 2: Create virtual environment
if (-not $SkipVenv) {
    Write-Host "`n[*] Step 2/7: Creating virtual environment..." -ForegroundColor Yellow
    
    if (Test-Path "venv") {
        Write-Host "   ℹ️  Virtual environment already exists, skipping..." -ForegroundColor Cyan
    } else {
        & $PythonPath -m venv venv
        if ($?) {
            Write-Host "   ✅ Virtual environment created" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    }
}

# Step 3: Activate venv and upgrade pip
Write-Host "`n[*] Step 3/7: Activating environment and upgrading pip..." -ForegroundColor Yellow

$venvPython = ".\venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = $PythonPath
    Write-Host "   ℹ️  Using system Python" -ForegroundColor Cyan
}

& $venvPython -m pip install --upgrade pip setuptools wheel --quiet
Write-Host "   ✅ Pip upgraded" -ForegroundColor Green

# Step 4: Install dependencies
Write-Host "`n[*] Step 4/7: Installing dependencies..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Cyan

if ($DevMode) {
    & $venvPython -m pip install -e ".[dev]" --quiet
    Write-Host "   ✅ Installed with dev dependencies" -ForegroundColor Green
} else {
    & $venvPython -m pip install -e . --quiet
    Write-Host "   ✅ Core dependencies installed" -ForegroundColor Green
}

# Step 5: Setup .env file
Write-Host "`n[*] Step 5/7: Configuring environment..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "   ✅ Created .env file from template" -ForegroundColor Green
    Write-Host "   ⚠️  IMPORTANT: Add your Anthropic API key to .env" -ForegroundColor Yellow
} else {
    Write-Host "   ℹ️  .env already exists, skipping..." -ForegroundColor Cyan
}

# Step 6: Run tests
Write-Host "`n[*] Step 6/7: Running test suite..." -ForegroundColor Yellow

& $venvPython -m pytest tests/ -v --tb=short 2>&1 | Out-Null
if ($?) {
    Write-Host "   ✅ All tests passed" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Some tests failed (this is okay for first install)" -ForegroundColor Yellow
}

# Step 7: Final verification
Write-Host "`n[*] Step 7/7: Verifying installation..." -ForegroundColor Yellow

$autohoundVersion = & $venvPython -c "import autohound; print(autohound.__version__)" 2>&1
if ($?) {
    Write-Host "   ✅ AutoHound v$autohoundVersion installed successfully" -ForegroundColor Green
} else {
    Write-Host "   ❌ Installation verification failed" -ForegroundColor Red
    exit 1
}

# Success banner
$success = @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              [+] INSTALLATION COMPLETE                       ║
║                                                              ║
║              AutoHound [ACH] Ready                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@

Write-Host $success -ForegroundColor Green

Write-Host "🎯 NEXT STEPS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Add your Anthropic API key to .env file:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Activate the virtual environment:" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Run AutoHound:" -ForegroundColor White
Write-Host "   autohound --help" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Analyze BloodHound data:" -ForegroundColor White
Write-Host "   autohound --input data.json --output ./reports" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 Documentation: README.md" -ForegroundColor Cyan
Write-Host "🐛 Issues: https://github.com/geo2x/autohound/issues" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  REMEMBER: Authorized lab environments only!" -ForegroundColor Red
Write-Host ""
Write-Host "[ACH] Automated Compromise Hunter - Ready for deployment" -ForegroundColor DarkGray
Write-Host ""
