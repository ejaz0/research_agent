FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CONVERSATION_DB_PATH=/app/data/research_agent.sqlite3

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md main.py ./
COPY briefing ./briefing
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN pip install --upgrade pip \
    && pip install .

RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl --fail http://127.0.0.1:8000/api/health || exit 1

CMD ["uvicorn", "briefing.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
