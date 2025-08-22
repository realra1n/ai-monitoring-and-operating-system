FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app.py ./app.py
COPY frontend ./frontend

# Create models directory
RUN mkdir -p models

# OpenTelemetry configuration
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4318 \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_SERVICE_NAME=mnist-cnn-demo \
    OTEL_SERVICE_NAMESPACE=oneservice \
    OTEL_SERVICE_VERSION=1.0.0 \
    OTEL_RESOURCE_ATTRIBUTES="deployment.environment=test,service.instance.id=mnist-demo-1"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/status || exit 1

EXPOSE 8001

# Use non-root user for security
RUN useradd -r -s /bin/false appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
