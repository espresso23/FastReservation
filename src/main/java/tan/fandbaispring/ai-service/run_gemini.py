#!/usr/bin/env python3
"""
Script to run Gemini AI service
"""

import os
import sys
import subprocess
import uvicorn
from pathlib import Path

def main():
    """Run Gemini AI service"""
    print("🚀 Starting Gemini AI Service...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📝 Please create .env file from env_example.txt")
        print("💡 Copy env_example.txt to .env and fill in your API keys")
        return
    
    # Check if required packages are installed
    try:
        import fastapi
        import uvicorn
        import langchain_google_genai
        import chromadb
        import psycopg2
        print("✅ All required packages are installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("📦 Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully")
    
    # Run the service
    print("🌐 Starting Gemini AI service on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        uvicorn.run(
            "ai_service_gemini:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Gemini AI service stopped")

if __name__ == "__main__":
    main()
