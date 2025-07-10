ARG POETRY_VER=2.1.3

# Use a multi-stage build to optimize the image size and dependencies
FROM python:3.12.2-slim AS base
ARG POETRY_VER
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# Poetry stage - install poetry
FROM base AS poetry
ARG POETRY_VER
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VER} && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Build stage - install dependencies directly with poetry
FROM poetry AS build
# Explicitly copy poetry.lock first to ensure it's used
COPY poetry.lock pyproject.toml ./
RUN /root/.local/bin/poetry config virtualenvs.create false && \
    /root/.local/bin/poetry install --no-interaction --no-ansi --without dev --no-root

# Final runtime stage
FROM python:3.12.2-slim AS runtime
ARG MCP_PORT="8080"
ENV MCP_PORT=${MCP_PORT} \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy installed Python packages from build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy application code
COPY mcp_tools /app/mcp_tools

# Clean up any unnecessary files
RUN find /app -type d -name "__pycache__" -exec rm -rf {} + && \
    find /app -type f -name "*.pyc" -delete

# Run the agent
CMD ["python", "-m", "mcp_tools"]