from fastapi import APIRouter, Depends, UploadFile, File
from ...schemas.auth import User
from ...schemas.sdk import SDKStartReq, SDKMetricReq, SDKLogReq, SDKTraceReq, SDKFinishReq
from ...services.auth import get_current_user
from ...services import runs as run_svc
from ...services import storage as storage_svc
from ...core.config import settings

router = APIRouter()


@router.post("/start")
async def sdk_start(body: SDKStartReq, current: User = Depends(get_current_user)):
    if current.tenant != body.tenant:
        from fastapi import HTTPException
        raise HTTPException(403, detail="Tenant mismatch")
    run_id = run_svc.create_run(current.tenant, body.run_name, body.framework or "unknown", body.tags or {})
    return {"run_id": run_id}


@router.post("/metric")
async def sdk_metric(body: SDKMetricReq, current: User = Depends(get_current_user)):
    rid = body.run_id or (run_svc.RUNS[-1]["id"] if run_svc.RUNS else None)
    if rid is None:
        return {"ok": True}
    run_svc.add_metric(rid, body.model_dump())
    return {"ok": True}


@router.post("/log")
async def sdk_log(body: SDKLogReq, current: User = Depends(get_current_user)):
    rid = body.run_id or (run_svc.RUNS[-1]["id"] if run_svc.RUNS else None)
    if rid is None:
        return {"ok": True}
    run_svc.add_log(rid, body.level, body.msg, body.ts)
    return {"ok": True}


@router.post("/trace")
async def sdk_trace(body: SDKTraceReq, current: User = Depends(get_current_user)):
    # acknowledged; OTel traces are sent out-of-band to Jaeger
    return {"ok": True}


@router.post("/artifact")
async def sdk_artifact(run_id: int | None = None, file: UploadFile = File(...), current: User = Depends(get_current_user)):
    rid = run_id or (run_svc.RUNS[-1]["id"] if run_svc.RUNS else None)
    if rid is None:
        return {"ok": True, "stored": False}
    data = await file.read()
    key = f"runs/{rid}/{file.filename}"
    client = storage_svc.get_minio_client()
    stored = storage_svc.put_artifact(client, key, data)
    if stored:
        return {"ok": True, "bucket": settings.MINIO_BUCKET, "key": key}
    return {"ok": True, "stored": False}


@router.post("/finish")
async def sdk_finish(body: SDKFinishReq, current: User = Depends(get_current_user)):
    run_svc.finish_run(body.run_id, body.status, body.ts)
    return {"ok": True}
