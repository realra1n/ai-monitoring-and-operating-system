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
VERSIONS_DIR = ASSETS_DIR / "versions"

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
    # Serve the default version if configured; fallback to embedded agent.py
    default_ver = (VERSIONS_DIR / 'default.txt').read_text(encoding='utf-8').strip() if (VERSIONS_DIR / 'default.txt').exists() else ''
    if default_ver:
        vp = VERSIONS_DIR / default_ver / 'agent.py'
        if vp.exists():
            return Response(vp.read_text(encoding='utf-8'), media_type='text/x-python')
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


# ----- Version management -----
class AgentVersion(BaseModel):
    version: str
    exporters: Dict[str, Dict[str, Any]] | None = None


@router.get('/versions', response_model=List[AgentVersion])
async def list_versions(current: User = Depends(get_current_user)):
    out: List[AgentVersion] = []
    if not VERSIONS_DIR.exists():
        return out
    for d in sorted([p for p in VERSIONS_DIR.iterdir() if p.is_dir()]):
        ver = d.name
        # read exporters info by executing file content and summarizing EXPORTERS.releases only
        agent_file = d / 'agent.py'
        exporters = None
        if agent_file.exists():
            try:
                src = agent_file.read_text(encoding='utf-8')
                env: Dict[str, Any] = {}
                exec(src, {}, env)
                raw = env.get('EXPORTERS')
                if isinstance(raw, dict):
                    exporters = {}
                    for k, v in raw.items():
                        if isinstance(v, dict) and isinstance(v.get('releases'), dict):
                            exporters[k] = {"releases": v['releases']}
            except Exception:
                exporters = None
        out.append(AgentVersion(version=ver, exporters=exporters))
    return out


@router.get('/versions/default')
async def get_default_version(current: User = Depends(get_current_user)):
    f = VERSIONS_DIR / 'default.txt'
    ver = f.read_text(encoding='utf-8').strip() if f.exists() else ''
    return {"default": ver}


class SetDefaultReq(BaseModel):
    version: str


@router.post('/versions/default')
async def set_default_version(req: SetDefaultReq, current: User = Depends(get_current_user)):
    d = VERSIONS_DIR / req.version
    if not d.exists() or not (d / 'agent.py').exists():
        raise HTTPException(status_code=400, detail='version not found')
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    (VERSIONS_DIR / 'default.txt').write_text(req.version + "\n", encoding='utf-8')
    return {"ok": True, "default": req.version}


@router.get('/assets/{version}/agent.py')
async def get_versioned_agent(version: str):
    p = VERSIONS_DIR / version / 'agent.py'
    if not p.exists():
        raise HTTPException(status_code=404, detail='agent.py not found for version')
    return Response(p.read_text(encoding='utf-8'), media_type='text/x-python')
