# syntax=docker/dockerfile:1
# The model is trained and quality-gated in CI *before* this build;
# the image only packages the approved model + the API.

# ── Build stage: install dependencies ──────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

# ── Runtime stage: small image, non-root user ──────────────────────────────
FROM python:3.12-slim
ARG GIT_SHA=local
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/models/model.joblib \
    GIT_SHA=${GIT_SHA} \
    PORT=8000
LABEL org.opencontainers.image.title="churn-guard" \
      org.opencontainers.image.revision="${GIT_SHA}"

RUN useradd --create-home --uid 10001 app
COPY --from=builder /install /usr/local
COPY models/model.joblib /app/models/model.joblib
USER app
WORKDIR /app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ[\"PORT\"]}/health')"

# PORT is set by the platform (Render uses 10000); exec so uvicorn receives stop signals.
CMD ["sh", "-c", "exec uvicorn churn.api:app --host 0.0.0.0 --port ${PORT}"]
