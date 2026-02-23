# Railway-friendly backend image: build with context = backend/
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure app package is importable when running alembic/uvicorn (e.g. Railway)
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run alembic migrations then start the application (Railway uses PORT env)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
