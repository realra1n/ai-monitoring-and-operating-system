# OneService-AI-Observation-System (MVP)

This repo contains a runnable MVP for an AI observability platform (Datadog-like) with:
- Frontend: native HTML/CSS/JS (iframe embeds for Grafana/Netron)
- Backend: FastAPI with demo auth, runs, SDK ingestion
- Stack via Docker Compose: Postgres, MinIO, OpenSearch, Prometheus + Thanos, Grafana, Jaeger, OTel Collector
- Python SDK: monitor_sdk with example training script

Quickstart (macOS/Linux):
1) make -C oneservice up
2) Open:
	- Frontend http://localhost:8080
	- Backend API docs http://localhost:8000/api/docs
	- Grafana http://localhost:3000 (admin/admin)
	- Jaeger http://localhost:16686

Login demo:
- email: demo@oneservice.local
- password: demo123

SDK demo:
- python -m venv .venv && source .venv/bin/activate
- pip install -r oneservice/backend/requirements.txt
- pip install -e oneservice/monitor_sdk
- export ONESERVICE_URL=http://localhost:8000
- export ONESERVICE_TOKEN=tok-demo
- python oneservice/monitor_sdk/examples/train_example.py

More details in oneservice/README.txt. Prompts and specifications are under PROMPTS/.