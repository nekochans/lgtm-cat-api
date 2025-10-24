ARG PYTHON_VERSION=3.12.4

FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /src

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /bin/uv

RUN uv sync --frozen --no-dev --no-install-project

FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 appuser && \
    chown -R appuser:appuser /app

COPY --from=builder /src/.venv /app/.venv

COPY ./src/ .

RUN chown -R appuser:appuser /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]