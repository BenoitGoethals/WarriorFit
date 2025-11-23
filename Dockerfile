FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


WORKDIR /app

# Copy dependency definition files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache

# Copy the rest of the application code
COPY . .

# Add the virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port defined in app.py (DEFAULT_PORT = 8000)
EXPOSE 8000


CMD ["shiny", "run", "--host", "0.0.0.0", "--port", "8000", "ui/app.py"]
