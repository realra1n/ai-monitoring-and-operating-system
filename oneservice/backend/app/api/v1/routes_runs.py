from fastapi import APIRouter, Depends, HTTPException
from ...schemas.auth import User
from ...services.auth import get_current_user
from ...services import runs as run_svc

router = APIRouter()


@router.get("")
async def list_runs(current: User = Depends(get_current_user)):
    return run_svc.list_runs_for_tenant(current.tenant)


@router.get("/{run_id}")
async def get_run(run_id: int, current: User = Depends(get_current_user)):
    r = run_svc.get_run_for_tenant(run_id, current.tenant)
    if not r:
        raise HTTPException(404, detail="Run not found")
    return r


@router.get("/{run_id}/metrics")
async def run_metrics(run_id: int, name: str = "loss", by: str = "step", current: User = Depends(get_current_user)):
    return run_svc.get_run_metrics(run_id, name, by)


@router.get("/{run_id}/logs")
async def run_logs(run_id: int, query: str | None = None, follow: bool = False, current: User = Depends(get_current_user)):
    return run_svc.get_run_logs(run_id, query, follow)
