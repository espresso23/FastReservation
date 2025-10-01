#!/bin/bash

echo "🚀 Starting AI Service..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "✅ Python found"
echo

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Please create .env file from env_example.txt"
    echo "💡 Copy env_example.txt to .env and fill in your API keys"
    exit 1
fi

echo "✅ .env file found"
echo

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn, langchain_google_genai, chromadb, psycopg2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    python3 install_dependencies.py
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

echo "✅ Dependencies ready"
echo

# Ask user which service to run
echo "Which AI service do you want to run?"
echo "1. Gemini AI Service (ai_service_gemini.py)"
echo "2. OpenAI AI Service (ai_service_openai.py)"
echo
read -p "Enter your choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo "🚀 Starting Gemini AI Service..."
    python3 run_gemini.py
elif [ "$choice" = "2" ]; then
    echo "🚀 Starting OpenAI AI Service..."
    python3 run_openai.py
else
    echo "❌ Invalid choice. Please run the script again."
    exit 1
fi
