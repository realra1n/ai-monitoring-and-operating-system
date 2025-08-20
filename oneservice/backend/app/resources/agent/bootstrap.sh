#!/usr/bin/env sh
set -e
BACKEND_URL="${BACKEND_URL:-http://oneservice-backend:8000}"
TOKEN="${TOKEN:-tok-demo}"
AGENT_VERSION="${AGENT_VERSION:-}"
WORKDIR="/tmp/oneservice-agent"
mkdir -p "$WORKDIR"
cd "$WORKDIR"
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
# Install python and deps if needed (Debian/Ubuntu/musl minimal best-effort)
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found; attempting to install..." >&2
  if command -v apk >/dev/null 2>&1; then apk add --no-cache python3 py3-pip; 
  elif command -v apt-get >/dev/null 2>&1; then apt-get update && apt-get install -y --no-install-recommends python3 python3-pip; 
  elif command -v microdnf >/dev/null 2>&1; then microdnf install -y python3 python3-pip; 
  else echo "Please ensure python3 is installed." >&2; fi
fi
python3 -m pip install --no-cache-dir --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install --no-cache-dir psutil requests pyyaml >/dev/null 2>&1
# Run agent with default yaml
exec python3 agent.py --backend "$BACKEND_URL" --token "$TOKEN" --config agent.yaml
