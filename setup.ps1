# AutoHound Project Setup Script
# AutoHound Setup Script - Run from project root directory

Write-Host "Setting up AutoHound project structure..." -ForegroundColor Cyan

# Create directory structure
$dirs = @(
    "autohound",
    "autohound/ingestor",
    "autohound/serializer", 
    "autohound/reasoning",
    "autohound/reporting",
    "autohound/utils",
    "tests",
    "tests/fixtures",
    "docs",
    "examples"
)

foreach ($dir in $dirs) {
    New-Item -Path $dir -ItemType Directory -Force | Out-Null
    Write-Host "? Created $dir" -ForegroundColor Green
}

Write-Host "
Project structure ready!" -ForegroundColor Green
Write-Host "Next: Restart Rovo Dev from this directory" -ForegroundColor Yellow
