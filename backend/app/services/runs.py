import math
import time
from typing import Dict, Optional
from ..models.memory import RUNS, RUN_LOGS, RUN_METRICS


def list_runs_for_tenant(tenant: str):
    return [r for r in RUNS if r["tenant_id"] == tenant]


def get_run_for_tenant(run_id: int, tenant: str):
    for r in RUNS:
        if r["id"] == run_id and r["tenant_id"] == tenant:
            return r
    return None


def get_run_metrics(run_id: int, name: str, by: str):
    if run_id in RUN_METRICS:
        series_points = [p for p in RUN_METRICS[run_id] if p.get("name") == name]
        points = [{by: p.get("step") or p.get("epoch") or idx + 1, "value": p.get("value", 0.0)} for idx, p in enumerate(series_points)]
        return {"series": [{"name": name, "points": points}]}
    # fallback demo
    points = []
    for i in range(1, 51):
        val = 1.0 / i if name == "loss" else min(0.5 + math.log(i+1)/5, 0.99)
        points.append({by: i, "value": val})
    return {"series": [{"name": name, "points": points}]}


def get_run_logs(run_id: int, query: Optional[str], follow: bool):
    logs = RUN_LOGS.get(run_id) or [
        {"ts": int(time.time()) - 10, "level": "INFO", "msg": "loading dataset shard-1"},
        {"ts": int(time.time()) - 5, "level": "INFO", "msg": "epoch 1 loss=0.52 acc=0.81"},
        {"ts": int(time.time()) - 1, "level": "WARN", "msg": "grad norm high"},
    ]
    if query:
        logs = [l for l in logs if query.lower() in l["msg"].lower()]
    return {"items": logs, "follow": follow}


def create_run(tenant: str, name: str, framework: str, tags: Dict[str, str]):
    run_id = int(time.time())
    RUNS.append({
        "id": run_id,
        "tenant_id": tenant,
        "project_id": 1,
        "name": name,
        "status": "running",
        "framework": framework or "unknown",
        "params_json": {},
        "start_ts": int(time.time()),
        "end_ts": None,
        "tags_json": tags or {},
    })
    RUN_METRICS[run_id] = []
    RUN_LOGS[run_id] = []
    return run_id


def add_metric(run_id: int, payload: dict):
    RUN_METRICS.setdefault(run_id, []).append(payload)


def add_log(run_id: int, level: str, msg: str, ts: Optional[int]):
    RUN_LOGS.setdefault(run_id, []).append({"level": level, "msg": msg, "ts": ts or int(time.time())})


def finish_run(run_id: Optional[int], status: str, ts: Optional[int]):
    rid = run_id or (RUNS[-1]["id"] if RUNS else None)
    if rid is None:
        return
    for r in RUNS:
        if r["id"] == rid:
            r["status"] = status
            r["end_ts"] = ts or int(time.time())
            break
