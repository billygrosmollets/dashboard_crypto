# ================================================
# PowerShell Deployment Script for Windows
# Crypto Portfolio Dashboard
# ================================================

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Crypto Portfolio Dashboard - Deployment Script" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "❌ ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env from .env.example:" -ForegroundColor Yellow
    Write-Host "  copy .env.example .env" -ForegroundColor Yellow
    Write-Host "  notepad .env" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker ps | Out-Null
} catch {
    Write-Host "❌ ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "🏗️  Building Docker images..." -ForegroundColor Green
docker-compose build --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🛑 Stopping old containers..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "🚀 Starting new containers..." -ForegroundColor Green
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""

# Get local IP address
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"} | Select-Object -First 1).IPAddress

Write-Host "📊 Access your application:" -ForegroundColor Cyan
Write-Host "  • From this PC:         http://localhost" -ForegroundColor White
if ($localIP) {
    Write-Host "  • From local network:   http://$localIP" -ForegroundColor White
}
Write-Host ""

Write-Host "📋 Container Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "💡 Useful commands:" -ForegroundColor Yellow
Write-Host "  • View logs:      docker-compose logs -f" -ForegroundColor White
Write-Host "  • Stop app:       docker-compose down" -ForegroundColor White
Write-Host "  • Restart:        docker-compose restart" -ForegroundColor White
Write-Host ""
