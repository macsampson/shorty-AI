# Shorty AI - One-Time Setup for Native Windows Development
# Run this once before using start-all.ps1

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ComfyUIPath = "O:\dev\ComfyUI"
$CondaEnv = "shorty-ai"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Shorty AI - Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# -------------------------------------------
# 1. Create conda environment for the API
# -------------------------------------------
Write-Host "[1/5] Setting up conda environment '$CondaEnv'..." -ForegroundColor Yellow

# Check if conda is available
$condaAvailable = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaAvailable) {
    Write-Host "  ERROR: conda not found. Install Miniconda from https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Red
    exit 1
}

# Create env if it doesn't exist
$envExists = conda env list 2>&1 | Select-String -Pattern "^$CondaEnv\s"
if (-not $envExists) {
    Write-Host "  Creating conda env '$CondaEnv' with Python 3.11..." -ForegroundColor Gray
    conda create -n $CondaEnv python=3.11 -y
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to create conda environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Conda environment created" -ForegroundColor Green
} else {
    Write-Host "  Conda environment '$CondaEnv' already exists" -ForegroundColor Green
}

# Activate the environment
Write-Host "  Activating '$CondaEnv'..." -ForegroundColor Gray
conda activate $CondaEnv

# -------------------------------------------
# 2. Install API Python dependencies
# -------------------------------------------
Write-Host ""
Write-Host "[2/5] Installing API Python dependencies into '$CondaEnv'..." -ForegroundColor Yellow

Set-Location $ProjectRoot

# Install PyTorch with CUDA first
Write-Host "  Installing PyTorch with CUDA 12.1..." -ForegroundColor Gray
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install remaining API deps
pip install -r api/requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARNING: Some API dependencies failed to install" -ForegroundColor Red
} else {
    Write-Host "  API dependencies installed" -ForegroundColor Green
}

# Note: aeneas (forced alignment) is optional - only needed for Shorty pipeline captions
# It requires espeak C library which is difficult to build on Windows
# VidiGen pipeline uses Whisper for word-level timestamps instead

# -------------------------------------------
# 3. Frontend Node modules (Vite)
# -------------------------------------------
Write-Host ""
Write-Host "[3/5] Installing frontend dependencies..." -ForegroundColor Yellow

Set-Location "$ProjectRoot\frontend"
bun i
if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARNING: npm install failed" -ForegroundColor Red
} else {
    Write-Host "  Frontend dependencies installed" -ForegroundColor Green
}

# -------------------------------------------
# 4. ComfyUI custom nodes (uses its own env)
# -------------------------------------------
Write-Host ""
Write-Host "[4/5] Setting up ComfyUI..." -ForegroundColor Yellow

if (Test-Path $ComfyUIPath) {
    # Install LTX-2 VRAM Management custom nodes
    $CustomNodesPath = "$ComfyUIPath\custom_nodes"
    $LTX2VRAMPath = "$CustomNodesPath\ComfyUI_LTX-2_VRAM_Memory_Management"

    if (-not (Test-Path $LTX2VRAMPath)) {
        Write-Host "  Installing LTX-2 VRAM Management nodes..." -ForegroundColor Gray
        Set-Location $CustomNodesPath
        git clone https://github.com/RandomInternetPreson/ComfyUI_LTX-2_VRAM_Memory_Management.git
    } else {
        Write-Host "  LTX-2 VRAM nodes already installed" -ForegroundColor Gray
    }

    # Check for LTX-2 model
    $ModelPath = "$ComfyUIPath\models\checkpoints\ltx-2-19b-distilled-fp8.safetensors"
    if (-not (Test-Path $ModelPath)) {
        Write-Host "  WARNING: LTX-2 model not found at $ModelPath" -ForegroundColor Red
        Write-Host "  Run: .\scripts\download_ltx2.ps1  (or download manually from HuggingFace)" -ForegroundColor Red
    } else {
        Write-Host "  LTX-2 model found" -ForegroundColor Green
    }

    Write-Host "  ComfyUI setup complete (uses its own Python env)" -ForegroundColor Green
} else {
    Write-Host "  WARNING: ComfyUI not found at $ComfyUIPath" -ForegroundColor Red
    Write-Host "  Clone it: git clone https://github.com/comfyanonymous/ComfyUI.git $ComfyUIPath" -ForegroundColor Red
}

# -------------------------------------------
# 5. Ollama model
# -------------------------------------------
Write-Host ""
Write-Host "[5/5] Checking Ollama..." -ForegroundColor Yellow

$ollamaAvailable = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaAvailable) {
    $models = ollama list 2>&1
    if ($models -match "gemma3:12b") {
        Write-Host "  gemma3:12b model ready" -ForegroundColor Green
    } else {
        Write-Host "  Pulling gemma3:12b..." -ForegroundColor Gray
        ollama pull gemma3:12b
    }
} else {
    Write-Host "  WARNING: Ollama not found. Install from https://ollama.com" -ForegroundColor Red
}

# -------------------------------------------
# Create generations directory
# -------------------------------------------
$GenerationsDir = "$ProjectRoot\generations"
New-Item -ItemType Directory -Force -Path "$GenerationsDir\images" | Out-Null
New-Item -ItemType Directory -Force -Path "$GenerationsDir\speech" | Out-Null
New-Item -ItemType Directory -Force -Path "$GenerationsDir\videos" | Out-Null
New-Item -ItemType Directory -Force -Path "$GenerationsDir\scripts" | Out-Null

# -------------------------------------------
# Summary
# -------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Conda env: $CondaEnv" -ForegroundColor White
Write-Host "  Activate:  conda activate $CondaEnv" -ForegroundColor Gray
Write-Host ""
Write-Host "  To start all services:" -ForegroundColor White
Write-Host "    .\scripts\start-all.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  Services:" -ForegroundColor White
Write-Host "    Frontend:  http://localhost:3000" -ForegroundColor Gray
Write-Host "    API:       http://localhost:8000" -ForegroundColor Gray
Write-Host "    ComfyUI:   http://localhost:8188" -ForegroundColor Gray
Write-Host "    Ollama:    http://localhost:11434" -ForegroundColor Gray
Write-Host ""

Set-Location $ProjectRoot
