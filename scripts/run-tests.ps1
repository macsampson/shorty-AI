# VidiGen AI - Test Runner
# Usage:
#   .\scripts\run-tests.ps1           # Unit tests only (excludes smoke)
#   .\scripts\run-tests.ps1 -Smoke    # Smoke tests only
#   .\scripts\run-tests.ps1 -All      # All tests
#   .\scripts\run-tests.ps1 -Coverage # Unit tests with coverage report

param(
    [switch]$Smoke,
    [switch]$All,
    [switch]$Coverage
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $ProjectRoot

try {
    if ($Smoke) {
        Write-Host "Running smoke tests..." -ForegroundColor Cyan
        python -m pytest tests/smoke/ -m smoke -v --tb=short
    }
    elseif ($All) {
        Write-Host "Running all tests..." -ForegroundColor Cyan
        python -m pytest tests/ -v --tb=short
    }
    elseif ($Coverage) {
        Write-Host "Running unit tests with coverage..." -ForegroundColor Cyan
        python -m pytest tests/ --ignore=tests/smoke -v --tb=short --cov --cov-report=term-missing
    }
    else {
        Write-Host "Running unit tests..." -ForegroundColor Cyan
        python -m pytest tests/ --ignore=tests/smoke -v --tb=short
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nAll tests passed!" -ForegroundColor Green
    } else {
        Write-Host "`nSome tests failed!" -ForegroundColor Red
    }
}
finally {
    Pop-Location
}
