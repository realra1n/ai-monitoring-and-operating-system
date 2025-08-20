OneService-AI-Observation-System (MVP)

Start stack:
- make -C oneservice up

Open:
- Frontend: http://localhost:8080
- Backend API docs: http://localhost:8000/api/docs
- Grafana: http://localhost:3000 (admin/admin)
- Jaeger: http://localhost:16686

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
