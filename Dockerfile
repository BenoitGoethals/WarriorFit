# Use Python 3.13 as the base image
FROM python:3.13-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    # Add /app to PYTHONPATH so python can find the 'warriorfit' package
    PYTHONPATH="/app"

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

# Install the project itself (if configured as a package)
RUN uv sync --frozen

# Expose the port
EXPOSE 8000

# Run the Shiny app
# Pointing to warriorfit/app.py instead of just app.py
CMD ["shiny", "run", "--host", "0.0.0.0", "--port", "8000", "warriorfit/app.py"]