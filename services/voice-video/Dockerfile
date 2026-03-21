# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.source="https://github.com/fgdiaz-jr/diversefocus-ia"
LABEL org.opencontainers.image.description="DiverseFocus-IA Voice/Video Service"

WORKDIR /app

# ffmpeg is required by OpenAI Whisper and yt-dlp
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY src/ ./src/

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && mkdir -p /app/tmp && chown appuser:appgroup /app/tmp
USER appuser

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
