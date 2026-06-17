FROM docker.io/library/python:3.11-slim

WORKDIR /app

# Build argument for workers (1 for dev, 4 for prod)
ARG WORKERS=1
ENV WORKERS=${WORKERS}

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/app/database /app/app/config /app/logs

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS}