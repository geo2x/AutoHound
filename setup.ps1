# BloodHound AI Project Setup Script
# Run this from C:\Users\gordo\Projects\BloodHound-AI

Write-Host "Setting up BloodHound AI project structure..." -ForegroundColor Cyan

# Create directory structure
$dirs = @(
    "bloodhound_ai",
    "bloodhound_ai/ingestor",
    "bloodhound_ai/serializer", 
    "bloodhound_ai/reasoning",
    "bloodhound_ai/reporting",
    "bloodhound_ai/utils",
    "tests",
    "tests/fixtures",
    "docs",
    "examples"
)

foreach ($dir in $dirs) {
    New-Item -Path $dir -ItemType Directory -Force | Out-Null
    Write-Host "✓ Created $dir" -ForegroundColor Green
}

Write-Host "
Project structure ready!" -ForegroundColor Green
Write-Host "Next: Restart Rovo Dev from this directory" -ForegroundColor Yellow
