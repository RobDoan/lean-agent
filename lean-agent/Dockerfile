# v0.2.0 backend service. Mac + Linux only (per design §9).
FROM python:3.12-slim

# curl for healthcheck; uv for dependency resolution.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Layer 1: deps (changes less frequently).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Layer 2: source (changes more frequently).
COPY src/ ./src/
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["uvicorn", "lean_agent.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
