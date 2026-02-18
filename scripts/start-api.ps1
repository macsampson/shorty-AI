# Shorty AI - Start FastAPI Backend

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting Shorty AI API..." -ForegroundColor Cyan

conda activate shorty-ai
Set-Location $ProjectRoot
python -m api.main
