#!/usr/bin/env sh
set -e

# Start agent in background to expose node_exporter for this container (deterministic path)
(
  set -e
  BACKEND_URL="${BACKEND_URL:-http://oneservice-backend:8000}"
  TOKEN="${TOKEN:-tok-demo}"
  SERVICE_NAME="${SERVICE_NAME:-oneservice-frontend}"
  ENV_NAME="${ENV_NAME:-dev}"
  TENANT="${TENANT:-demo}"
  NODE_EXPORTER_PORT="${NODE_EXPORTER_PORT:-9100}"
  echo "[agent] waiting for backend at $BACKEND_URL..."
  for i in $(seq 1 30); do
    if curl -fsS "$BACKEND_URL/api/agents/versions" >/dev/null 2>&1; then break; fi
    sleep 2
  done
  mkdir -p /tmp/oneservice-agent
  cd /tmp/oneservice-agent
  echo "[agent] downloading assets..."
  curl -fsSL "$BACKEND_URL/api/agents/assets/agent.py" -o agent.py
  curl -fsSL "$BACKEND_URL/api/agents/assets/agent.yaml" -o agent.yaml
  chmod +x agent.py
  echo "[agent] applying overrides (service=$SERVICE_NAME, env=$ENV_NAME, tenant=$TENANT, port=$NODE_EXPORTER_PORT)"
  python3 - <<'PY'
import os, yaml
p = '/tmp/oneservice-agent/agent.yaml'
with open(p,'r',encoding='utf-8') as f:
    cfg = yaml.safe_load(f) or {}
cfg.setdefault('labels', {})
cfg['tenant'] = os.getenv('TENANT','demo')
cfg['labels']['service'] = os.getenv('SERVICE_NAME','oneservice-frontend')
cfg['labels']['env'] = os.getenv('ENV_NAME','dev')
exp = cfg.setdefault('exporters', {})
ne = exp.setdefault('node_exporter', {})
ne['enabled'] = True
try:
    ne['port'] = int(os.getenv('NODE_EXPORTER_PORT','9100'))
except Exception:
    pass
with open(p,'w',encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, sort_keys=False)
PY
  echo "[agent] starting..."
  nohup python3 agent.py --backend "$BACKEND_URL" --token "$TOKEN" --config agent.yaml >> /tmp/agent.log 2>&1 &
  echo "[agent] started (pid=$!), logging to /tmp/agent.log"
) &

exec nginx -g 'daemon off;'
