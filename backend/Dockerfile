FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system deps (optional) and Python deps
# If wheels are available, these aren't needed, keeping image small and simple
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application code
COPY backend /app/backend

# Create non-root user
RUN useradd -m appuser
USER appuser

WORKDIR /app/backend

EXPOSE 8080

ENV PORT=8080
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
