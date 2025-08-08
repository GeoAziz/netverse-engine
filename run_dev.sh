#!/bin/bash

# Development runner for Zizo_NetVerse Backend
# This script helps run the backend in development mode

echo "🚀 Starting Zizo_NetVerse Backend in Development Mode..."

# Navigate to backend directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from parent directory..."
    cp ../.env .env 2>/dev/null || echo "⚠️ No .env file found. Please create one with required environment variables."
fi

# Install/update dependencies
echo "📚 Installing/updating dependencies..."
pip install -r requirements.txt

# Start the FastAPI server
echo "🔥 Starting Zizo_NetVerse Backend Engine..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔌 WebSocket endpoint: ws://localhost:8000/api/v1/ws/logs/network"
echo ""
echo "💡 Note: Packet capture requires root privileges. Use 'sudo' if needed."
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
