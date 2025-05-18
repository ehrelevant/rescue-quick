FROM ghcr.io/astral-sh/uv:debian

WORKDIR /app

# Set DEBUG to passed DEBUG argument
ARG DEBUG
ENV DEBUG=$DEBUG

# Install system dependencies
RUN apt-get update && \
    apt-get install ffmpeg libsm6 libxext6 curl -y \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm

# Copy npm lockfiles
COPY package-lock.json package.json /app/

# Install Node dependencies
RUN npm install

# Copy uv lockfiles
COPY uv.lock pyproject.toml /app/

# Install Python dependencies
# Cache is not saved to save space on the production server
RUN if [ "$DEBUG" = "False" ] ; then \
        uv sync --locked --no-dev --no-cache; \
    else \
        uv sync --locked --no-cache; \
    fi
        
# Copy all of the other project files
COPY . /app

# Set entrypoint to be executable
RUN chmod +x /app/entrypoint.sh

# Expose port 3000 and serve via WSGI
EXPOSE 3000

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

CMD uv run --locked --no-dev --no-cache gunicorn config.wsgi:application --bind 0.0.0.0:3000
