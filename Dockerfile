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

# Copy lockfiles
COPY uv.lock pyproject.toml /app/

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY . /app

# Copy Tailwind output file
COPY --from=builder /app/core/static/core/css/output.css /app/core/static/core/css/output.css 

# Collect static files
RUN uv run manage.py collectstatic --no-input -i input.css -i django-browser-reload

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 3000 and serve via WSGI
EXPOSE 3000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:3000"]