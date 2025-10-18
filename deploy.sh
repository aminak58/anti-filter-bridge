#!/bin/bash

# Anti-Filter Bridge Deployment Script
# This script deploys the application to various platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to deploy to Railway
deploy_railway() {
    print_status "Deploying to Railway..."
    
    if ! command_exists railway; then
        print_error "Railway CLI not found. Installing..."
        npm install -g @railway/cli
    fi
    
    railway login
    railway up
    print_success "Railway deployment completed!"
}

# Function to deploy to Heroku
deploy_heroku() {
    print_status "Deploying to Heroku..."
    
    if ! command_exists heroku; then
        print_error "Heroku CLI not found. Please install it first."
        return 1
    fi
    
    # Create Heroku app if it doesn't exist
    if ! heroku apps:info anti-filter-bridge >/dev/null 2>&1; then
        heroku create anti-filter-bridge
    fi
    
    git push heroku main
    print_success "Heroku deployment completed!"
}

# Function to deploy to Render
deploy_render() {
    print_status "Deploying to Render..."
    
    # Render deployment is done through GitHub integration
    print_warning "Render deployment requires GitHub integration."
    print_status "Please connect your GitHub repository to Render and deploy manually."
    print_status "Repository: https://github.com/aminak58/anti-filter-bridge"
}

# Function to build Docker image
build_docker() {
    print_status "Building Docker image..."
    
    if ! command_exists docker; then
        print_error "Docker not found. Please install Docker first."
        return 1
    fi
    
    docker build -t anti-filter-bridge:latest .
    print_success "Docker image built successfully!"
}

# Function to run locally with Docker
run_docker() {
    print_status "Running with Docker Compose..."
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose not found. Please install Docker Compose first."
        return 1
    fi
    
    docker-compose up -d
    print_success "Application running with Docker Compose!"
}

# Main deployment function
main() {
    echo "=========================================="
    echo "🚀 Anti-Filter Bridge Deployment Script"
    echo "=========================================="
    
    case "${1:-all}" in
        "railway")
            deploy_railway
            ;;
        "heroku")
            deploy_heroku
            ;;
        "render")
            deploy_render
            ;;
        "docker")
            build_docker
            ;;
        "run")
            run_docker
            ;;
        "all")
            print_status "Deploying to all platforms..."
            deploy_railway
            deploy_heroku
            deploy_render
            build_docker
            ;;
        *)
            echo "Usage: $0 {railway|heroku|render|docker|run|all}"
            echo ""
            echo "Options:"
            echo "  railway  - Deploy to Railway"
            echo "  heroku   - Deploy to Heroku"
            echo "  render   - Deploy to Render"
            echo "  docker   - Build Docker image"
            echo "  run      - Run with Docker Compose"
            echo "  all      - Deploy to all platforms"
            exit 1
            ;;
    esac
    
    print_success "Deployment completed!"
}

# Run main function with all arguments
main "$@"
