# Shorty AI - Start ComfyUI
# Launches ComfyUI natively from the local installation

$ComfyUIPath = "O:\dev\ComfyUI"

Write-Host "Starting ComfyUI from $ComfyUIPath..." -ForegroundColor Cyan

Set-Location $ComfyUIPath

conda activate shorty-ai
pip install -r requirements.txt
python main.py --enable-manager
