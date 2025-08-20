from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List, Dict
import time
import os
from io import BytesIO

# Optional MinIO for artifact storage
try:
    from minio import Minio
except Exception:  # pragma: no cover
    Minio = None  # type: ignore

app = FastAPI(title="OneService Backend", openapi_url="/api/openapi.json", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# In-memory demo storage
TENANT = "demo"
USERS = {"demo@oneservice.local": {"password": "demo123", "role": "TENANT_ADMIN", "tenant": TENANT}}
TOKENS = {}
RUNS = [
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

# In-memory SDK data stores
RUN_METRICS: Dict[int, list] = {}
RUN_LOGS: Dict[int, list] = {}

# MinIO client (optional)
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minio123")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "artifacts")
minio_client = None
if Minio is not None:
    try:
        use_secure = MINIO_ENDPOINT.startswith("https://")
        endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
        minio_client = Minio(endpoint, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=use_secure)
        # ensure bucket exists
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
    except Exception:
        minio_client = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    email: str
    role: str
    tenant: str

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # allow demo API token for SDK
    if token == "tok-demo":
        return User(email="demo@oneservice.local", role="TENANT_ADMIN", tenant=TENANT)
    user_email = TOKENS.get(token)
    if not user_email or user_email not in USERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = USERS[user_email]
    return User(email=user_email, role=user["role"], tenant=user["tenant"])

@app.get("/api/health")
def health():
    return {"status": "ok", "ts": int(time.time())}

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = f"tok-{int(time.time()*1000)}-{form_data.username}"
    TOKENS[token] = form_data.username
    return Token(access_token=token)

@app.get("/api/runs")
async def list_runs(current: User = Depends(get_current_user)):
    return [r for r in RUNS if r["tenant_id"] == current.tenant]

@app.get("/api/runs/{run_id}")
async def get_run(run_id: int, current: User = Depends(get_current_user)):
    for r in RUNS:
        if r["id"] == run_id and r["tenant_id"] == current.tenant:
            return r
    raise HTTPException(404, detail="Run not found")

@app.get("/api/runs/{run_id}/metrics")
async def run_metrics(run_id: int, name: str = "loss", by: str = "step", current: User = Depends(get_current_user)):
    # if SDK provided metrics, serve them
    if run_id in RUN_METRICS:
        series_points = [p for p in RUN_METRICS[run_id] if p.get("name") == name]
        points = [{by: p.get("step") or p.get("epoch") or idx + 1, "value": p.get("value", 0.0)} for idx, p in enumerate(series_points)]
        return {"series": [{"name": name, "points": points}]}
    # fallback demo data
    import math
    points = []
    for i in range(1, 51):
        val = 1.0 / i if name == "loss" else min(0.5 + math.log(i+1)/5, 0.99)
        points.append({by: i, "value": val})
    return {"series": [{"name": name, "points": points}]}

@app.get("/api/runs/{run_id}/logs")
async def run_logs(run_id: int, query: Optional[str] = None, follow: bool = False, current: User = Depends(get_current_user)):
    logs = RUN_LOGS.get(run_id) or [
        {"ts": int(time.time()) - 10, "level": "INFO", "msg": "loading dataset shard-1"},
        {"ts": int(time.time()) - 5, "level": "INFO", "msg": "epoch 1 loss=0.52 acc=0.81"},
        {"ts": int(time.time()) - 1, "level": "WARN", "msg": "grad norm high"},
    ]
    if query:
        logs = [l for l in logs if query.lower() in l["msg"].lower()]
    return {"items": logs, "follow": follow}

@app.get("/api/dashboards")
async def dashboards(current: User = Depends(get_current_user)):
    grafana = os.environ.get("GRAFANA_URL", "http://localhost:3000")
    return [
        {"id": 1, "name": "System Overview", "url": f"{grafana}/d/000000012/node-exporter-full"},
        {"id": 2, "name": "K8S Overview", "url": f"{grafana}/d/k8s/kubernetes"},
    ]

@app.get("/")
async def root():
    return {"name": "OneService Backend", "docs": "/api/docs"}


# ---------- SDK ingestion endpoints ----------

class SDKStartReq(BaseModel):
    tenant: str
    project: str
    run_name: str
    framework: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


@app.post("/api/sdk/start")
async def sdk_start(body: SDKStartReq, current: User = Depends(get_current_user)):
    if current.tenant != body.tenant:
        raise HTTPException(403, detail="Tenant mismatch")
    run_id = int(time.time())
    RUNS.append({
        "id": run_id,
        "tenant_id": current.tenant,
        "project_id": 1,
        "name": body.run_name,
        "status": "running",
        "framework": body.framework or "unknown",
        "params_json": {},
        "start_ts": int(time.time()),
        "end_ts": None,
        "tags_json": body.tags or {},
    })
    RUN_METRICS[run_id] = []
    RUN_LOGS[run_id] = []
    return {"run_id": run_id}


class SDKMetricReq(BaseModel):
    run_id: Optional[int] = None
    name: str
    value: float
    step: Optional[int] = None
    epoch: Optional[int] = None
    ts: Optional[int] = None


@app.post("/api/sdk/metric")
async def sdk_metric(body: SDKMetricReq, current: User = Depends(get_current_user)):
    rid = body.run_id or (RUNS[-1]["id"] if RUNS else int(time.time()))
    RUN_METRICS.setdefault(rid, []).append(body.model_dump())
    return {"ok": True}


class SDKLogReq(BaseModel):
    run_id: Optional[int] = None
    level: str = "INFO"
    msg: str
    ts: Optional[int] = None


@app.post("/api/sdk/log")
async def sdk_log(body: SDKLogReq, current: User = Depends(get_current_user)):
    rid = body.run_id or (RUNS[-1]["id"] if RUNS else int(time.time()))
    RUN_LOGS.setdefault(rid, []).append({"level": body.level, "msg": body.msg, "ts": body.ts or int(time.time())})
    return {"ok": True}


class SDKTraceReq(BaseModel):
    run_id: Optional[int] = None
    name: str
    duration_ms: int
    ts: Optional[int] = None


@app.post("/api/sdk/trace")
async def sdk_trace(body: SDKTraceReq, current: User = Depends(get_current_user)):
    # In MVP we only acknowledge; OTel is expected to send to Jaeger separately
    return {"ok": True}


@app.post("/api/sdk/artifact")
async def sdk_artifact(run_id: Optional[int] = None, file: UploadFile = File(...), current: User = Depends(get_current_user)):
    rid = run_id or (RUNS[-1]["id"] if RUNS else int(time.time()))
    data = await file.read()
    key = f"runs/{rid}/{file.filename}"
    if minio_client:
        try:
            minio_client.put_object(MINIO_BUCKET, key, BytesIO(data), length=len(data))
            return {"ok": True, "bucket": MINIO_BUCKET, "key": key}
        except Exception:
            pass
    # fallback: discard but ack
    return {"ok": True, "stored": False}


class SDKFinishReq(BaseModel):
    run_id: Optional[int] = None
    status: str = "success"
    ts: Optional[int] = None


@app.post("/api/sdk/finish")
async def sdk_finish(body: SDKFinishReq, current: User = Depends(get_current_user)):
    rid = body.run_id or (RUNS[-1]["id"] if RUNS else None)
    if rid is not None:
        for r in RUNS:
            if r["id"] == rid:
                r["status"] = body.status
                r["end_ts"] = body.ts or int(time.time())
                break
    return {"ok": True}
