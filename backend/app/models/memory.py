import time
from typing import Dict, List
from ..core.config import settings

# In-memory demo storage (kept for MVP)
TENANT = settings.DEMO_TENANT
USERS = {
    "demo@oneservice.local": {
        "id": 1,
        "name": "Demo Admin",
        "password": "demo123",
        "role": "TENANT_ADMIN",
        "tenant": TENANT,
    }
}
TOKENS: Dict[str, str] = {}
RUNS: List[dict] = [
    {
        "id": 1,
        "tenant_id": TENANT,
        "project_id": 1,
        "name": "demo-run-a",
        "status": "running",
        "framework": "pytorch",
        "params_json": {"lr": 1e-3},
        "start_ts": int(time.time()) - 120,
        "end_ts": None,
        "tags_json": {"exp": "A"},
    },
    {
        "id": 2,
        "tenant_id": TENANT,
        "project_id": 1,
        "name": "demo-run-b",
        "status": "success",
        "framework": "tensorflow",
        "params_json": {"lr": 5e-4},
        "start_ts": int(time.time()) - 3600,
        "end_ts": int(time.time()) - 3000,
        "tags_json": {"exp": "B"},
    },
]

RUN_METRICS: Dict[int, list] = {}
RUN_LOGS: Dict[int, list] = {}
