#!/bin/bash

# obojobs Backend - Start local development server
cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

source venv/bin/activate
echo "🚀 Starting Flask development server on http://localhost:5002"
flask run --port 5002 --debug
