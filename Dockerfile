# Use Python 3.13 as the base image
FROM python:3.13-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    # Add /app to PYTHONPATH so python can find the 'warriorfit' package
    PYTHONPATH="/app"

# WF_SECRET_KEY must be provided at runtime, e.g.:
#   docker run -e WF_SECRET_KEY=<your-secret> ...
# or via docker-compose environment / secrets.
# It is intentionally NOT set here so it is never baked into the image.
ARG WF_SECRET_KEY
ENV WF_SECRET_KEY=${WF_SECRET_KEY}

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# This creates a virtual environment in /app/.venv
RUN uv sync --frozen --no-install-project

# Add the virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the application code
COPY . .

# APP_ENV and APP_PORT are provided at runtime via docker run -e
# APP_ENV: "production" or "test"
# APP_PORT: 8000 (prod) or 8501 (test)
ENV APP_ENV=production \
    APP_PORT=8000

# Install the project itself (if configured as a package)
RUN uv sync --frozen

# Expose both prod and test ports (documentation only)
EXPOSE 8000 8501

# Run the Shiny app — port is read from APP_PORT at runtime
CMD ["sh", "-c", "shiny run --host 0.0.0.0 --port ${APP_PORT} warriorfit/app.py"]