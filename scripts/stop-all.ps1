# Shorty AI - Stop All Services
# Stops all running Shorty AI services by port/process name

Write-Host "Stopping Shorty AI services..." -ForegroundColor Cyan

# Helper: kill process listening on a given port
function Stop-ServiceOnPort {
    param([int]$Port, [string]$Name)
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conn) {
        $pids = $conn.OwningProcess | Select-Object -Unique
        foreach ($pid in $pids) {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  Stopping $Name (PID $pid) on port $Port..." -ForegroundColor Yellow
                Stop-Process -Id $pid -Force
            }
        }
    } else {
        Write-Host "  $Name not running on port $Port" -ForegroundColor DarkGray
    }
}

# Stop services by port
Stop-ServiceOnPort -Port 8000 -Name "API"
Stop-ServiceOnPort -Port 3000 -Name "Frontend"
Stop-ServiceOnPort -Port 8188 -Name "ComfyUI"
Stop-ServiceOnPort -Port 8008 -Name "Flux"

# Stop Ollama by process name (it doesn't always bind a fixed port immediately)
$ollama = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($ollama) {
    Write-Host "  Stopping Ollama..." -ForegroundColor Yellow
    Stop-Process -Name "ollama" -Force
} else {
    Write-Host "  Ollama not running" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "All services stopped." -ForegroundColor Green
