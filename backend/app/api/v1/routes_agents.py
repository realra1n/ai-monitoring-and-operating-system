from fastapi import APIRouter, Depends, Response, HTTPException, UploadFile, File, Form
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
    # Merge endpoints per tenant so multiple agents/services can coexist
    os.makedirs(FILE_SD_DIR, exist_ok=True)
    path = os.path.join(FILE_SD_DIR, f"{req.tenant}.json")
    existing: list[dict] = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                existing = json.load(f) or []
        except Exception:
            existing = []
    def key_of(item: dict) -> tuple:
        labels = item.get('labels', {}) or {}
        # Stable key: tuple of sorted label items
        return tuple(sorted(labels.items()))

    merged: dict[tuple, dict] = {key_of(it): it for it in existing if isinstance(it, dict)}
    for t in req.endpoints:
        item = {
            "labels": {"job": t.job, **(t.labels or {})},
            "targets": t.targets,
        }
        merged[key_of(item)] = item
    payload = list(merged.values())
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    return {"ok": True, "file": path, "count": len(payload)}


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
async def list_versions():
    # Only support v1 moving forward
    out: List[AgentVersion] = []
    if not VERSIONS_DIR.exists():
        return out
    for d in sorted([p for p in VERSIONS_DIR.iterdir() if p.is_dir() and p.name == 'v1']):
        ver = d.name
        # Read exporters info by statically parsing EXPORTERS and extracting the 'releases' dicts
        agent_file = d / 'agent.py'
        exporters = None
        if agent_file.exists():
            try:
                import ast
                src = agent_file.read_text(encoding='utf-8')
                mod = ast.parse(src)
                exporters = {}
                for node in mod.body:
                    if isinstance(node, ast.Assign):
                        for t in node.targets:
                            if isinstance(t, ast.Name) and t.id == 'EXPORTERS' and isinstance(node.value, (ast.Dict,)):
                                # node.value is a dict of exporters
                                for k_node, v_node in zip(node.value.keys, node.value.values):
                                    if isinstance(k_node, ast.Constant) and isinstance(k_node.value, str) and isinstance(v_node, ast.Dict):
                                        name = k_node.value
                                        releases = None
                                        # find 'releases' key in v_node
                                        for kk, vv in zip(v_node.keys, v_node.values):
                                            if isinstance(kk, ast.Constant) and kk.value == 'releases' and isinstance(vv, ast.Dict):
                                                # convert releases dict literals
                                                rel_map: Dict[str, Any] = {}
                                                for rk, rv in zip(vv.keys, vv.values):
                                                    if isinstance(rk, ast.Constant) and isinstance(rv, ast.Constant):
                                                        rel_map[str(rk.value)] = str(rv.value)
                                                releases = rel_map
                                                break
                                        exporters[name] = {"releases": releases or {}}
                                break
            except Exception:
                exporters = None
        out.append(AgentVersion(version=ver, exporters=exporters))
    return out


@router.get('/versions/default')
async def get_default_version():
    f = VERSIONS_DIR / 'default.txt'
    ver = f.read_text(encoding='utf-8').strip() if f.exists() else ''
    return {"default": ver}


class SetDefaultReq(BaseModel):
    version: str


@router.post('/versions/default')
async def set_default_version(req: SetDefaultReq, current: User = Depends(get_current_user)):
    # Lock default to v1 only
    if req.version != 'v1':
        raise HTTPException(status_code=400, detail='only v1 is supported')
    d = VERSIONS_DIR / req.version
    if not d.exists() or not (d / 'agent.py').exists():
        raise HTTPException(status_code=400, detail='version not found')
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    (VERSIONS_DIR / 'default.txt').write_text(req.version + "\n", encoding='utf-8')
    return {"ok": True, "default": req.version}


@router.get('/assets/{version}/agent.py')
async def get_versioned_agent(version: str):
    if version != 'v1':
        raise HTTPException(status_code=404, detail='only v1 is available')
    p = VERSIONS_DIR / version / 'agent.py'
    if not p.exists():
        raise HTTPException(status_code=404, detail='agent.py not found for version')
    return Response(p.read_text(encoding='utf-8'), media_type='text/x-python')


@router.post('/versions/upload')
async def upload_version(version: str = Form(...), file: UploadFile = File(...), current: User = Depends(get_current_user)):
    # Expect a zip containing an agent.py at root
    import zipfile, io
    data = await file.read()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
            if 'agent.py' not in names and not any(n.endswith('/agent.py') for n in names):
                raise HTTPException(status_code=400, detail='zip must contain agent.py')
            target = VERSIONS_DIR / version
            target.mkdir(parents=True, exist_ok=True)
            z.extractall(target)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail='invalid zip')
    return {"ok": True, "version": version}


@router.delete('/versions/{version}')
async def delete_version(version: str, current: User = Depends(get_current_user)):
    d = VERSIONS_DIR / version
    if not d.exists():
        raise HTTPException(status_code=404, detail='version not found')
    # prevent deleting default
    defv = (VERSIONS_DIR / 'default.txt').read_text(encoding='utf-8').strip() if (VERSIONS_DIR / 'default.txt').exists() else ''
    if version == defv:
        raise HTTPException(status_code=400, detail='cannot delete default version')
    import shutil
    shutil.rmtree(d)
    return {"ok": True}
