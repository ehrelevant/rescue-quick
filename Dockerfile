FROM node:lts AS builder

WORKDIR /app

# Copy lockfiles
COPY package-lock.json package.json /app/

# Install Node dependencies
RUN npm install

# Copy other files
COPY ./core /app/core

# Run Tailwind build script
RUN npm run build:tailwind

FROM ghcr.io/astral-sh/uv:debian

WORKDIR /app

# Set DEBUG to False to indicate a production environment on build
# This is also done to avoid unnecessary installation of django-browser-reload
ENV DEBUG=False

# Install system dependencies
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Copy lockfiles
COPY uv.lock pyproject.toml /app/

# Install Python dependencies
# Cache is not saved to save space on the production server
RUN uv sync --locked --no-dev --no-cache

# Copy all of the other project files
COPY . /app

# Copy Tailwind output file
COPY --from=builder /app/core/static/core/css/output.css /app/core/static/core/css/output.css 

# Collect static files
RUN uv run --locked --no-dev --no-cache manage.py collectstatic --no-input -i input.css

# Expose port 3000 and serve via WSGI
EXPOSE 3000

CMD uv run --locked --no-dev --no-cache gunicorn config.wsgi:application --bind 0.0.0.0:3000
