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

## SDK testing guide

Follow these steps to send demo metrics/logs/traces from the SDK and view them in the app.

1) Start the stack

```bash
make -C oneservice up
```

Wait until all containers are healthy (first run may take ~1–2 minutes to pull images).

2) Prepare a Python environment and install the SDK (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r oneservice/backend/requirements.txt
pip install -e oneservice/monitor_sdk
```

3) Configure SDK endpoint and token

Option A (demo token):

```bash
export ONESERVICE_URL=http://localhost:8000
export ONESERVICE_TOKEN=tok-demo
```

Option B (real token via API):

```bash
TOKEN=$(curl -s -X POST \
	-H 'Content-Type: application/x-www-form-urlencoded' \
	-d 'username=demo@oneservice.local&password=demo123' \
	http://localhost:8000/api/auth/login | jq -r .access_token)
export ONESERVICE_URL=http://localhost:8000
export ONESERVICE_TOKEN="$TOKEN"
```

4) Run the example training script

```bash
python oneservice/monitor_sdk/examples/train_example.py
```

The script logs loss/accuracy metrics, text logs, a simple span per step, and finishes the run.

5) Verify the results

- App UI: http://localhost:8080 → “训练监控” → you should see a run named "sdk-demo". Click 查看 to see loss points and logs.
- API (optional):
	- List runs:
		```bash
		curl -s http://localhost:8000/api/runs -H "Authorization: Bearer $ONESERVICE_TOKEN" | jq
		```
	- Metrics for a run (replace 1 with your run id):
		```bash
		curl -s "http://localhost:8000/api/runs/1/metrics?name=loss&by=step" -H "Authorization: Bearer $ONESERVICE_TOKEN" | jq
		```
	- Logs for a run:
		```bash
		curl -s http://localhost:8000/api/runs/1/logs -H "Authorization: Bearer $ONESERVICE_TOKEN" | jq
		```
- MinIO artifacts (if you call upload_artifact): http://localhost:9001 → login minio/minio123 → bucket "artifacts" → path runs/<run_id>/.
- Jaeger traces: http://localhost:16686 (the demo span endpoint is acknowledged by the backend; end-to-end OTel tracing to Jaeger can be wired later).

6) Optional: Upload an artifact

```python
from monitor_sdk import OneServiceRun
import os

run = OneServiceRun(
		base_url=os.environ['ONESERVICE_URL'],
		api_token=os.environ['ONESERVICE_TOKEN'],
		tenant='demo', project='demo-project', run_name='sdk-demo', framework='pytorch')

with open('hello.txt', 'w') as f: f.write('hello oneservice')
run.upload_artifact('hello.txt')
```

Artifacts will appear in MinIO bucket "artifacts" at runs/<run_id>/hello.txt.

### Troubleshooting

- 401 Unauthorized: ensure ONESERVICE_TOKEN is set and valid (use tok-demo for quick tests).
- Connection refused: verify the stack is running: `make -C oneservice ps` and `make -C oneservice logs`.
- Frontend shows empty runs: refresh after the SDK script completes; check API `/api/runs` for data.