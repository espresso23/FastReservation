@echo off
echo 🚀 Starting AI Service...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo 📝 Please create .env file from env_example.txt
    echo 💡 Copy env_example.txt to .env and fill in your API keys
    pause
    exit /b 1
)

echo ✅ .env file found
echo.

REM Install dependencies if needed
echo 📦 Checking dependencies...
python -c "import fastapi, uvicorn, langchain_google_genai, chromadb, psycopg2" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing dependencies...
    python install_dependencies.py
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

echo ✅ Dependencies ready
echo.

REM Ask user which service to run
echo Which AI service do you want to run?
echo 1. Gemini AI Service (ai_service_gemini.py)
echo 2. OpenAI AI Service (ai_service_openai.py)
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo 🚀 Starting Gemini AI Service...
    python run_gemini.py
) else if "%choice%"=="2" (
    echo 🚀 Starting OpenAI AI Service...
    python run_openai.py
) else (
    echo ❌ Invalid choice. Please run the script again.
    pause
    exit /b 1
)

pause
