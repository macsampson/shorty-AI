# Shorty AI - Start React Frontend (Vite)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting Shorty AI Frontend (Vite)..." -ForegroundColor Cyan

Set-Location "$ProjectRoot\frontend"
npm run dev
