#!/bin/sh
set -e

# Install dev dependencies (debugpy etc.) without modifying the prod image
pip install --no-cache-dir -r requirements-dev.txt

# Start Flask with hot-reload enabled.
# debugpy is started programmatically inside create_app() (only in the reloader's child process)
# so that breakpoints work AND hot-reload works simultaneously.
exec python -Xfrozen_modules=off -m flask --app app run --debug --host 0.0.0.0 --port 5002
