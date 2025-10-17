#!/bin/bash

# Anti-Filter Bridge - Automated Setup Script
# This script automates the installation and initial setup

set -e  # Exit on any error

echo "🚀 Anti-Filter Bridge - Automated Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python is installed
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Python $PYTHON_VERSION found"

# Check if pip is installed
echo "🔍 Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip."
    exit 1
fi
print_status "pip3 found"

# Check if OpenSSL is installed
echo "🔍 Checking OpenSSL installation..."
if ! command -v openssl &> /dev/null; then
    print_warning "OpenSSL not found. SSL certificate generation may fail."
    print_warning "Please install OpenSSL:"
    print_warning "  Ubuntu/Debian: sudo apt-get install openssl"
    print_warning "  CentOS/RHEL: sudo yum install openssl"
    print_warning "  macOS: brew install openssl"
else
    print_status "OpenSSL found"
fi

# Create virtual environment (optional)
echo "🔧 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -e .
print_status "Dependencies installed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p certs
print_status "Directories created"

# Generate SSL certificates
echo "🔐 Generating SSL certificates..."
if command -v openssl &> /dev/null; then
    python3 generate_certs.py
    print_status "SSL certificates generated"
else
    print_warning "Skipping SSL certificate generation (OpenSSL not found)"
fi

# Create environment file
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp env.example .env
    print_status "Environment file created from template"
    print_warning "Please edit .env file with your settings"
else
    print_status "Environment file already exists"
fi

# Run installation test
echo "🧪 Running installation test..."
python3 test_installation.py

# Final instructions
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration:"
echo "   nano .env"
echo ""
echo "2. Start the server:"
echo "   python -m anti_filter_bridge.server --certfile certs/cert.pem --keyfile certs/key.pem"
echo ""
echo "3. In another terminal, start the client:"
echo "   python client.py --server wss://localhost:8443 --local-port 1080"
echo ""
echo "4. Configure your browser to use SOCKS5 proxy:"
echo "   Address: 127.0.0.1"
echo "   Port: 1080"
echo ""
echo "For more information, see QUICKSTART.md"
