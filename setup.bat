@echo off
REM Anti-Filter Bridge - Automated Setup Script for Windows
REM This script automates the installation and initial setup

echo 🚀 Anti-Filter Bridge - Automated Setup
echo ======================================

REM Check if Python is installed
echo 🔍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python found

REM Check if pip is installed
echo 🔍 Checking pip installation...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is not installed. Please install pip.
    pause
    exit /b 1
)
echo ✅ pip found

REM Check if OpenSSL is installed (optional)
echo 🔍 Checking OpenSSL installation...
openssl version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  OpenSSL not found. SSL certificate generation may fail.
    echo Please install OpenSSL or use Git Bash which includes OpenSSL.
) else (
    echo ✅ OpenSSL found
)

REM Create virtual environment
echo 🔧 Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated

REM Install dependencies
echo 📦 Installing dependencies...
python -m pip install --upgrade pip
pip install -e .
echo ✅ Dependencies installed

REM Create necessary directories
echo 📁 Creating directories...
if not exist "logs" mkdir logs
if not exist "certs" mkdir certs
echo ✅ Directories created

REM Generate SSL certificates
echo 🔐 Generating SSL certificates...
openssl version >nul 2>&1
if not errorlevel 1 (
    python generate_certs.py
    echo ✅ SSL certificates generated
) else (
    echo ⚠️  Skipping SSL certificate generation (OpenSSL not found)
    echo You can generate certificates later using Git Bash or WSL
)

REM Create environment file
echo ⚙️  Setting up environment configuration...
if not exist ".env" (
    copy env.example .env
    echo ✅ Environment file created from template
    echo ⚠️  Please edit .env file with your settings
) else (
    echo ✅ Environment file already exists
)

REM Run installation test
echo 🧪 Running installation test...
python test_installation.py

REM Final instructions
echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Edit .env file with your configuration:
echo    notepad .env
echo.
echo 2. Start the server:
echo    python -m anti_filter_bridge.server --certfile certs\cert.pem --keyfile certs\key.pem
echo.
echo 3. In another command prompt, start the client:
echo    python client.py --server wss://localhost:8443 --local-port 1080
echo.
echo 4. Configure your browser to use SOCKS5 proxy:
echo    Address: 127.0.0.1
echo    Port: 1080
echo.
echo For more information, see QUICKSTART.md
echo.
pause
