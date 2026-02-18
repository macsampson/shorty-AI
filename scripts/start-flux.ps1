# Shorty AI - Start Flux Image Generation Service

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting Flux image generation service..." -ForegroundColor Cyan

Set-Location "$ProjectRoot\flux"
uvicorn api:app --host 0.0.0.0 --port 8008 --reload
