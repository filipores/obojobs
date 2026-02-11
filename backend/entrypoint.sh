#!/bin/sh
set -e

# Run database migrations
flask db upgrade --directory migrations

# Start gunicorn
exec gunicorn --bind 0.0.0.0:5002 --workers 2 --timeout 120 --access-logfile - --preload wsgi:app
