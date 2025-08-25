# PowerShell script to start MCP Tools with Docker

Write-Host "🚀 Starting MCP Tools Server with Docker..." -ForegroundColor Green

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop first:" -ForegroundColor Red
    Write-Host "   https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "   After installation, restart your terminal and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker info > $null 2>&1
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Build and start the container
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
docker-compose build

Write-Host "🚀 Starting MCP Tools server..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "⏳ Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ Server is running successfully!" -ForegroundColor Green
    Write-Host "🌐 Health endpoint: http://localhost:8080/health" -ForegroundColor Cyan
    Write-Host "🎨 Drawings endpoint: http://localhost:8080/drawings/sse" -ForegroundColor Cyan
    Write-Host "📊 NocoDB endpoint: http://localhost:8080/nocodb/sse" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Server might still be starting. Please wait a moment and try again." -ForegroundColor Yellow
    Write-Host "   You can check the logs with: docker-compose logs -f" -ForegroundColor Yellow
}

Write-Host "`n📝 Useful commands:" -ForegroundColor Magenta
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop server: docker-compose down" -ForegroundColor White
Write-Host "   Restart server: docker-compose restart" -ForegroundColor White
