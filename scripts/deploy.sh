#!/bin/bash

# Stock Research Chatbot - Production Deployment Script
# This script builds and deploys the application using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Parse command line arguments
BUILD_ONLY="false"
NO_CACHE="false"
ENVIRONMENT="production"

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            BUILD_ONLY="true"
            shift
            ;;
        --no-cache)
            NO_CACHE="true"
            shift
            ;;
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build-only    Only build images, don't start containers"
            echo "  --no-cache      Build without using cache"
            echo "  --env ENV       Set environment (production|staging) [default: production]"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_status "Deploying Stock Research Chatbot..."
print_status "Environment: $ENVIRONMENT"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is required but not installed"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is required but not installed"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Creating .env file from template..."
    
    if [ -f ".env.template" ]; then
        cp .env.template .env
        print_warning "Please edit .env file with your API keys before deploying"
        exit 1
    else
        print_error ".env.template file not found!"
        exit 1
    fi
fi

# Build Docker images
print_status "Building Docker images..."

if [ "$NO_CACHE" = "true" ]; then
    docker-compose build --no-cache
else
    docker-compose build
fi

print_success "Docker images built successfully"

# If build-only flag is set, exit here
if [ "$BUILD_ONLY" = "true" ]; then
    print_success "Build completed. Use 'docker-compose up -d' to start the services."
    exit 0
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down

# Start the application
print_status "Starting application containers..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check if services are running
print_status "Checking service health..."

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API is healthy"
else
    print_warning "Backend API health check failed"
fi

# Check if Streamlit is running
if curl -f http://localhost:8501 > /dev/null 2>&1; then
    print_success "Streamlit frontend is running"
else
    print_warning "Streamlit frontend health check failed"
fi

print_success "Deployment completed!"
print_status ""
print_status "Services are running:"
print_status "- Backend API: http://localhost:8000"
print_status "- API Documentation: http://localhost:8000/docs"
print_status "- Streamlit Frontend: http://localhost:8501"
print_status ""
print_status "To view logs: docker-compose logs -f"
print_status "To stop services: docker-compose down"
print_status "To restart services: docker-compose restart"
