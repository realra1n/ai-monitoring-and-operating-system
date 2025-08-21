OTel stack overview

Components
- Grafana Alloy: OTLP receiver and processor (ports 4317/4318)
- Prometheus: metrics TSDB with OTLP HTTP receiver enabled (9090)
- Grafana Tempo: traces backend, stores in MinIO bucket `tempo` (3200)
- Grafana Loki: logs backend (3100)
- Grafana: dashboards and Explore (3000)

Data flow
- Apps send OTLP traces/metrics/logs to Alloy http://alloy:4318
- Alloy adds resource attrs, batches, tail-samples traces
- Alloy exports: metrics -> Prometheus (/api/v1/otlp), traces -> Tempo, logs -> Loki

Run
- docker compose up -d in this folder
- Access Grafana http://localhost:3000 (admin/admin)
