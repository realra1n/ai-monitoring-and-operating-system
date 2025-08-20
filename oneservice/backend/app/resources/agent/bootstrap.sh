#!/usr/bin/env sh
set -e
# Configurable env vars
BACKEND_URL="${BACKEND_URL:-}"
TOKEN="${TOKEN:-tok-demo}"
AGENT_VERSION="${AGENT_VERSION:-}"
# Optional overrides for agent.yaml
TENANT="${TENANT:-}"
SERVICE_NAME="${SERVICE_NAME:-}"
ENV_NAME="${ENV_NAME:-}"
NODE_EXPORTER_ENABLED="${NODE_EXPORTER_ENABLED:-true}"
NODE_EXPORTER_PORT="${NODE_EXPORTER_PORT:-}"

WORKDIR="/tmp/oneservice-agent"
mkdir -p "$WORKDIR"
cd "$WORKDIR"
# Auto-detect backend URL if not provided (resolve oneservice-backend to IP inside container)
if [ -z "$BACKEND_URL" ]; then
  host="$(getent hosts oneservice-backend 2>/dev/null | awk '{print $1}' | head -n1)"
  if [ -z "$host" ] && [ -f /etc/hosts ]; then
  host="$(awk '/[[:space:]]oneservice-backend(\.|[[:space:]]|$)/{print $1; exit}' /etc/hosts)"
  fi
  host="${host:-oneservice-backend}"
  BACKEND_URL="http://$host:8000"
fi
# Fetch agent.py (default or versioned) and default config
if [ -n "$AGENT_VERSION" ]; then
  curl -fsSL "$BACKEND_URL/api/agents/assets/$AGENT_VERSION/agent.py" -o agent.py || {
  echo "Specified AGENT_VERSION=$AGENT_VERSION not found; falling back to default" >&2; AGENT_VERSION=""; }
fi
if [ -z "$AGENT_VERSION" ]; then
  curl -fsSL "$BACKEND_URL/api/agents/assets/agent.py" -o agent.py
fi
curl -fsSL "$BACKEND_URL/api/agents/assets/agent.yaml" -o agent.yaml
chmod +x agent.py

# Install python and deps if needed (best-effort with OS packages to avoid building)
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found; attempting to install..." >&2
  if command -v apk >/dev/null 2>&1; then apk add --no-cache python3 py3-pip py3-psutil py3-requests py3-yaml; 
  elif command -v apt-get >/dev/null 2>&1; then apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-psutil python3-requests python3-yaml; 
  elif command -v microdnf >/dev/null 2>&1; then microdnf install -y python3 python3-pip python3-psutil python3-requests python3-pyyaml || true; 
  else echo "Please ensure python3 is installed." >&2; fi
fi
python3 -m pip install --no-cache-dir --upgrade pip >/dev/null 2>&1 || true
# Ensure deps present if OS packages unavailable
python3 - <<'PY'
import sys, subprocess
def ensure(pkg, mod=None):
  mod = mod or pkg
  try:
    __import__(mod)
  except Exception:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
for pkg,mod in [('psutil','psutil'),('requests','requests'),('pyyaml','yaml')]:
  ensure(pkg,mod)
PY

# Apply optional overrides to agent.yaml
python3 - <<'PY'
import os, yaml
cfg = {}
with open('agent.yaml','r',encoding='utf-8') as f:
  cfg = yaml.safe_load(f) or {}
cfg.setdefault('labels', {})
tenant = os.getenv('TENANT')
if tenant:
  cfg['tenant'] = tenant
svc = os.getenv('SERVICE_NAME')
if svc:
  cfg['labels']['service'] = svc
envn = os.getenv('ENV_NAME')
if envn:
  cfg['labels']['env'] = envn
exp = cfg.setdefault('exporters', {})
ne = exp.setdefault('node_exporter', {})
ne['enabled'] = str(os.getenv('NODE_EXPORTER_ENABLED','true')).lower() in ('1','true','yes','on')
port = os.getenv('NODE_EXPORTER_PORT')
if port:
  try:
    ne['port'] = int(port)
  except Exception:
    pass
with open('agent.yaml','w',encoding='utf-8') as f:
  yaml.safe_dump(cfg, f, sort_keys=False)
PY

# Run agent with yaml
exec python3 agent.py --backend "$BACKEND_URL" --token "$TOKEN" --config agent.yaml
