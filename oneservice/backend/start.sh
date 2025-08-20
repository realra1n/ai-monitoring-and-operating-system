#!/usr/bin/env sh
set -e

# Start agent in background to expose node_exporter for this container
(
  set -e
  export BACKEND_URL="${BACKEND_URL:-http://oneservice-backend:8000}"
  export TOKEN="${TOKEN:-tok-demo}"
  export SERVICE_NAME="oneservice-backend"
  export ENV_NAME="dev"
  export TENANT="demo"
  export NODE_EXPORTER_ENABLED=true
  export NODE_EXPORTER_PORT="${NODE_EXPORTER_PORT:-9100}"
  # Fetch and run via in-image resources for reliability
  cp -f app/resources/agent/agent.py /tmp/agent.py
  cp -f app/resources/agent/agent.yaml /tmp/agent.yaml || true
  chmod +x /tmp/agent.py
  # Apply overrides to agent.yaml
  python3 - <<'PY'
import os, yaml
path = '/tmp/agent.yaml'
try:
  with open(path,'r',encoding='utf-8') as f:
    cfg = yaml.safe_load(f) or {}
except FileNotFoundError:
  cfg = {'tenant':'demo','labels':{'service':'oneservice-backend','env':'dev'},'exporters':{'node_exporter':{'enabled':True,'port': int(os.getenv('NODE_EXPORTER_PORT','9100'))}}}
cfg.setdefault('labels', {})
cfg['tenant'] = os.getenv('TENANT', cfg.get('tenant','demo'))
cfg['labels']['service'] = os.getenv('SERVICE_NAME', cfg['labels'].get('service','oneservice-backend'))
cfg['labels']['env'] = os.getenv('ENV_NAME', cfg['labels'].get('env','dev'))
exp = cfg.setdefault('exporters', {})
ne = exp.setdefault('node_exporter', {})
ne['enabled'] = True
try:
  ne['port'] = int(os.getenv('NODE_EXPORTER_PORT', str(ne.get('port',9100))))
except Exception:
  ne['port'] = ne.get('port',9100)
with open(path,'w',encoding='utf-8') as f:
  yaml.safe_dump(cfg, f, sort_keys=False)
PY
  python3 -m pip install --no-cache-dir --upgrade pip >/dev/null 2>&1 || true
  python3 -m pip install --no-cache-dir psutil requests pyyaml >/dev/null 2>&1 || true
  nohup python3 /tmp/agent.py --backend "$BACKEND_URL" --token "$TOKEN" --config /tmp/agent.yaml >/tmp/backend-agent.log 2>&1 &
  echo "[backend] agent started, tail -f /tmp/backend-agent.log for details" >&2
) || echo "Agent failed to start; backend will continue" >&2

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
