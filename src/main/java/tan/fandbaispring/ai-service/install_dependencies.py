#!/usr/bin/env python3
"""
Script to install AI service dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("Installing AI service dependencies...")
    
    # Check if requirements.txt exists
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    try:
        # Install packages
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        
        print("Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Python 3.8+ is required!")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def main():
    """Main installation process"""
    print("AI Service Dependencies Installer")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if install_requirements():
        print("\nInstallation completed successfully!")
        print("\nNext steps:")
        print("1. Copy env_example.txt to .env")
        print("2. Fill in your API keys in .env file")
        print("3. Run: python run_gemini.py (for Gemini)")
        print("4. Or run: python run_openai.py (for OpenAI)")
    else:
        print("\nInstallation failed!")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()
