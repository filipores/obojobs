#!/bin/bash

# obojobs Backend - Local Development Setup
cd "$(dirname "$0")"

echo "🔧 Setting up local development environment..."

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔌 Activating virtual environment..."
source venv/bin/activate

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

source venv/bin/activate
echo "🚀 Starting Flask development server on http://localhost:5002"
flask run --port 5002 --debug

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate && flask run --port 5002 --debug"
echo ""
echo "Or for debugging in VSCode: Press F5"
