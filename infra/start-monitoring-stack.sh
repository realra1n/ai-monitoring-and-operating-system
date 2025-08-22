#!/bin/bash
set -e

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "Starting all monitoring services..."
docker-compose up -d

echo "Waiting for services to be healthy..."
# You can add more sophisticated health checks here
sleep 10

echo "Monitoring stack is up and running."
echo "Grafana: http://localhost:3000"
echo "Prometheus (Metrics): http://localhost:9090"
echo "Prometheus (OTLP): http://localhost:9091"
echo "Thanos Query: http://localhost:19191"
echo "Alloy UI: http://localhost:12345"
