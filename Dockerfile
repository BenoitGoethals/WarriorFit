# Use Python 3.13 slim image
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency definition files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen ensures we use exactly what is in uv.lock
# --no-dev omits development dependencies (optional, remove if you need dev tools)
RUN uv sync --frozen --no-cache

# Copy the rest of the application code
COPY . .

# Add the virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port defined in app.py (DEFAULT_PORT = 8000)
EXPOSE 8000

# Run the Shiny application
# Pointing to ui/app.py based on your project structure
CMD ["shiny", "run", "--host", "0.0.0.0", "--port", "8000", "ui/app.py"]
