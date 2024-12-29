# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory in container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY app/ ./app/

# Set environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:8000/healthz || exit 1

ENV PYTHONPATH=/app
ENV LOG_LEVEL=debug

# Command to run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--proxy-headers", "--timeout-keep-alive", "75", "--log-level", "debug"]
