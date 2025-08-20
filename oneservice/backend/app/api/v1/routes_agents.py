from fastapi import APIRouter, Depends, Response, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
from pathlib import Path

from ...schemas.auth import User
from ...services.auth import get_current_user

router = APIRouter()

FILE_SD_DIR = "/etc/prometheus/file_sd"  # mounted into Prometheus container
# In container, this file lives at /app/app/api/v1/routes_agents.py, so resources are at parents[2]/resources/agent
ASSETS_DIR = Path(__file__).resolve().parents[2] / "resources" / "agent"

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


@router.get('/assets/agent.py')
async def get_agent_py():
    # Serve the embedded agent implementation from resources
    p = ASSETS_DIR / 'agent.py'
    if not p.exists():
        raise HTTPException(status_code=404, detail="agent.py not found")
    return Response(p.read_text(encoding='utf-8'), media_type='text/x-python')


@router.get('/assets/agent.yaml')
async def get_agent_yaml():
    p = ASSETS_DIR / 'agent.yaml'
    if not p.exists():
        raise HTTPException(status_code=404, detail="agent.yaml not found")
    return Response(p.read_text(encoding='utf-8'), media_type='text/yaml')


@router.get('/install.sh')
async def get_install_script():
    p = ASSETS_DIR / 'bootstrap.sh'
    if not p.exists():
        raise HTTPException(status_code=404, detail="bootstrap not found")
    # Render as shell script with executable content
    return Response(p.read_text(encoding='utf-8'), media_type='text/x-sh')
