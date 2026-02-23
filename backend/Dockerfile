# Railway-friendly backend image: build with context = repo root (e.g. docker build -f backend/Dockerfile .)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend/ and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire backend into fixed path so app/ and alembic/ are at /app/backend
COPY backend/ /app/backend

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 8000

# Run migrations then start uvicorn on $PORT (shell form so ${PORT} expands)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
