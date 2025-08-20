from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os

from ...schemas.auth import User
from ...services.auth import get_current_user

router = APIRouter()

FILE_SD_DIR = "/etc/prometheus/file_sd"  # mounted into Prometheus container

class Target(BaseModel):
    job: str
    targets: List[str]
    labels: Dict[str, Any] | None = None

class AgentRegisterReq(BaseModel):
    tenant: str
    endpoints: List[Target]

@router.post('/register')
async def register_agent(req: AgentRegisterReq, current: User = Depends(get_current_user)):
    # In MVP, we write a single file per tenant to Prometheus file_sd directory
    os.makedirs(FILE_SD_DIR, exist_ok=True)
    path = os.path.join(FILE_SD_DIR, f"{req.tenant}.json")
    payload = []
    for t in req.endpoints:
        item = {
            "labels": {"job": t.job, **(t.labels or {})},
            "targets": t.targets,
        }
        payload.append(item)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    return {"ok": True, "file": path}
