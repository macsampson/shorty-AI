# Shorty AI - Start All Services
# Launches all services in separate windows for native development

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting Shorty AI services..." -ForegroundColor Cyan

# Start Ollama (if not already running)
$ollamaRunning = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaRunning) {
    Write-Host "  Starting Ollama..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-ollama.ps1"
    Start-Sleep -Seconds 2
} else {
    Write-Host "  Ollama already running" -ForegroundColor Green
}

# Start ComfyUI (uses its own Python env)
Write-Host "  Starting ComfyUI..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-comfyui.ps1"
Start-Sleep -Seconds 3

# Start API (activates shorty-ai conda env)
Write-Host "  Starting API..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-api.ps1"
Start-Sleep -Seconds 2

# Start Frontend (Node/Vite, no conda needed)
Write-Host "  Starting Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-frontend.ps1"

Write-Host ""
Write-Host "All services started!" -ForegroundColor Green
Write-Host "  API:      http://localhost:8000  (conda: shorty-ai)" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  ComfyUI:  http://localhost:8188" -ForegroundColor White
Write-Host "  Ollama:   http://localhost:11434" -ForegroundColor White

# Wait for services to initialize
Write-Host ""
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Run smoke tests
Write-Host "Running smoke tests..." -ForegroundColor Cyan
Push-Location $ProjectRoot
conda activate shorty-ai
python -m pytest tests/smoke/ -m smoke -v --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "All services verified!" -ForegroundColor Green
} else {
    Write-Host "Some services failed health check!" -ForegroundColor Red
}
Pop-Location
