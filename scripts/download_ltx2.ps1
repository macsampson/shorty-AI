# Download LTX-2 19B Distilled FP8 model (PowerShell version)

$ModelDir = ".\models\ltx2"
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null

Write-Host "Downloading LTX-2 19B Distilled FP8 model..." -ForegroundColor Cyan

Invoke-WebRequest `
    -Uri "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.safetensors" `
    -OutFile "$ModelDir\ltx-2-19b-distilled-fp8.safetensors"

Write-Host "Model download complete!" -ForegroundColor Green
Write-Host "Location: $ModelDir\ltx-2-19b-distilled-fp8.safetensors"
