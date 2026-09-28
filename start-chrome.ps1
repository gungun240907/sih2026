# Opens the full stack in Chrome: FastAPI backend + React dashboard + live page.
# Usage: powershell -ExecutionPolicy Bypass -File start-chrome.ps1
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$CHROME = 'C:\Program Files\Google\Chrome\Application\chrome.exe'

# 1) Backend (serves API + built React app on :8000)
$running = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if (-not $running) {
    Start-Process -FilePath 'python' `
        -ArgumentList '-m', 'uvicorn', 'app.main:app', '--port', '8000' `
        -WorkingDirectory "$ROOT\backend" -WindowStyle Minimized
    Write-Host 'Starting backend...'
    Start-Sleep -Seconds 12
}

# 2) Chrome: dashboard tab + live-scraping tab
& $CHROME 'http://localhost:8000/' 'http://localhost:8000/?view=live'
Write-Host 'Opened Chrome: dashboard + live scraping.'
