#!/bin/bash

# Banana Coin Trading API Server Startup Script

echo "🍌 Starting Banana Coin Trading API Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    # Windows
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    # Unix/Mac
    source venv/bin/activate
else
    echo "Error: Could not find virtual environment activation script"
    exit 1
fi

# Install requirements if needed
echo "Checking dependencies..."
pip install -q -r ../requirements.txt

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the server
echo "✅ Starting FastAPI server on http://0.0.0.0:8000"
echo "📊 View API docs at http://localhost:8000/docs"
echo ""

uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

