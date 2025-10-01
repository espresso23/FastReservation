# AI Service Startup Script for PowerShell
Write-Host "🚀 Starting AI Service..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "📝 Please create .env file from env_example.txt" -ForegroundColor Yellow
    Write-Host "💡 Copy env_example.txt to .env and fill in your API keys" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ .env file found" -ForegroundColor Green
Write-Host ""

# Install dependencies if needed
Write-Host "📦 Checking dependencies..." -ForegroundColor Blue
try {
    python -c "import fastapi, uvicorn, langchain_google_genai, chromadb, psycopg2" 2>$null
    Write-Host "✅ Dependencies ready" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Blue
    python install_dependencies.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""

# Ask user which service to run
Write-Host "Which AI service do you want to run?" -ForegroundColor Cyan
Write-Host "1. Gemini AI Service (ai_service_gemini.py)" -ForegroundColor White
Write-Host "2. OpenAI AI Service (ai_service_openai.py)" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter your choice (1 or 2)"

if ($choice -eq "1") {
    Write-Host "🚀 Starting Gemini AI Service..." -ForegroundColor Green
    Write-Host "🌐 Service will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "⏹️  Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    python run_gemini.py
} elseif ($choice -eq "2") {
    Write-Host "🚀 Starting OpenAI AI Service..." -ForegroundColor Green
    Write-Host "🌐 Service will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "⏹️  Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    python run_openai.py
} else {
    Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
