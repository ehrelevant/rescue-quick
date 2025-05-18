#!/bin/bash
set -e

# Build Tailwind CSS files
echo "Building Tailwind files..."
./node_modules/.bin/tailwindcss -i ./core/static/core/css/input.css -o ./core/static/core/css/output.css

# Collect static files
echo "Collecting static files..."
uv run --locked --no-dev --no-cache manage.py collectstatic --clear --no-input -i input.css 

# Execute command passed to the container
exec "$@"