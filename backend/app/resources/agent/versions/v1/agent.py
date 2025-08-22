#!/usr/bin/env python3
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil
import contextlib
import requests
import yaml

BASE_DIR = Path.home() / ".oneservice" / "exporters"
EXPORTERS = {
    "node_exporter": {
        "releases": {
            "linux-amd64": "https://github.com/prometheus/node_exporter/releases/download/v1.8.2/node_exporter-1.8.2.linux-amd64.tar.gz",
            "linux-arm64": "https://github.com/prometheus/node_exporter/releases/download/v1.8.2/node_exporter-1.8.2.linux-arm64.tar.gz",
            "darwin-amd64": "https://github.com/prometheus/node_exporter/releases/download/v1.8.2/node_exporter-1.8.2.darwin-amd64.tar.gz",
            "darwin-arm64": "https://github.com/prometheus/node_exporter/releases/download/v1.8.2/node_exporter-1.8.2.darwin-arm64.tar.gz",
        },
        "binary": "node_exporter",
        "args": lambda cfg: [f"--web.listen-address=:{cfg['port']}"]
    },
    "mysqld_exporter": {
        "releases": {
            "linux-amd64": "https://github.com/prometheus/mysqld_exporter/releases/download/v0.15.1/mysqld_exporter-0.15.1.linux-amd64.tar.gz",
            "linux-arm64": "https://github.com/prometheus/mysqld_exporter/releases/download/v0.15.1/mysqld_exporter-0.15.1.linux-arm64.tar.gz",
            "darwin-amd64": "https://github.com/prometheus/mysqld_exporter/releases/download/v0.15.1/mysqld_exporter-0.15.1.darwin-amd64.tar.gz",
            "darwin-arm64": "https://github.com/prometheus/mysqld_exporter/releases/download/v0.15.1/mysqld_exporter-0.15.1.darwin-arm64.tar.gz",
        },
        "binary": "mysqld_exporter",
        "args": lambda cfg: [f"--web.listen-address=:{cfg['port']}", f"--mysqld.address=127.0.0.1:3306", f"--mysqld.username=root"]
    }
}


def http_ok(url, token=None, json=None, method="POST"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = requests.request(method, url, headers=h, data=(None if json is None else __import__('json').dumps(json)), timeout=5)
    return r.ok, (r.json() if r.headers.get('content-type','').startswith('application/json') else r.text)


def ensure_exporter(name: str) -> Path:
    os_name = platform.system().lower()
    arch = platform.machine().lower()
    if os_name.startswith("linux"):
        key = f"linux-{'arm64' if 'arm' in arch or 'aarch64' in arch else 'amd64'}"
    elif os_name.startswith("darwin"):
        key = f"darwin-{'arm64' if 'arm' in arch or 'aarch64' in arch else 'amd64'}"
    else:
        key = None
    rel = EXPORTERS[name]["releases"].get(key or "linux-amd64")
    if not rel:
        raise RuntimeError(f"unsupported OS for {name}: {os_name}")
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    tar_path = BASE_DIR / f"{name}.tar.gz"
    bin_dir = BASE_DIR / name
    bin_path = bin_dir / EXPORTERS[name]["binary"]
    if bin_path.exists():
        return bin_path
    # Download
    import urllib.request, tarfile
    urllib.request.urlretrieve(rel, tar_path)
    bin_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(bin_dir)
    # Move binary to predictable path (first dir/*/binary)
    found = None
    for root, dirs, files in os.walk(bin_dir):
        if EXPORTERS[name]["binary"] in files:
            found = Path(root) / EXPORTERS[name]["binary"]
            break
    if not found:
        raise RuntimeError(f"binary not found after extracting {name}")
    shutil.move(str(found), str(bin_path))
    os.chmod(bin_path, 0o755)
    return bin_path


def is_listening(port: int) -> bool:
    for c in psutil.net_connections(kind='inet'):
        if c.laddr and c.laddr.port == port and c.status == psutil.CONN_LISTEN:
            return True
    return False


def run_exporter(name: str, cfg: dict):
    if not cfg.get('enabled', False):
        return None
    port = int(cfg.get('port', 0))
    if not port:
        raise RuntimeError(f"{name}: port is required")
    if is_listening(port):
        return None
    bin_path = ensure_exporter(name)
    args = [str(bin_path)] + EXPORTERS[name]["args"](cfg)
    env = os.environ.copy()
    if name == 'mysqld_exporter' and cfg.get('dsn'):
        env['DATA_SOURCE_NAME'] = cfg['dsn']
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, env=env)
    return proc


def register_with_backend(backend: str, token: str, tenant: str, labels: dict, exporters_cfg: dict):
    targets = []
    for name, ecfg in exporters_cfg.items():
        if not ecfg.get('enabled'): continue
        port = int(ecfg.get('port', 0))
        if not port: continue
        targets.append({"job": name, "targets": [f"{get_host_ip()}:{port}"], "labels": labels})
    ok, out = http_ok(f"{backend.rstrip('/')}/api/agents/register", token=token, json={
        "tenant": tenant,
        "endpoints": targets,
    })
    if not ok:
        print("register failed:", out, file=sys.stderr)


def get_host_ip() -> str:
    # Best effort: return first non-loopback IPv4
    for iface, addrs in psutil.net_if_addrs().items():
        for a in addrs:
            if getattr(a, 'family', None) == getattr(psutil, 'AF_LINK', 17):
                continue
            if a.address and ':' not in a.address and not a.address.startswith('127.'):
                return a.address
    return '127.0.0.1'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='agent.yaml')
    ap.add_argument('--backend', required=True, help='OneService Backend URL, e.g. http://localhost:8000')
    ap.add_argument('--token', required=True, help='Bearer token (tok-demo or login-acquired)')
    args = ap.parse_args()

    with open(args.config, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}

    tenant = cfg.get('tenant', 'demo')
    labels = cfg.get('labels', {})
    exporters_cfg = cfg.get('exporters', {})

    procs = []
    try:
        for name in EXPORTERS.keys():
            ecfg = exporters_cfg.get(name, {})
            p = run_exporter(name, ecfg)
            if p: procs.append(p)
        # register targets so Prometheus starts scraping via backend
        register_with_backend(args.backend, args.token, tenant, labels, exporters_cfg)
        # keep running and supervise
        while True:
            time.sleep(5)
            # simple liveness check; restart if crashed
            for i, p in enumerate(list(procs)):
                if p.poll() is not None:
                    # crashed—attempt restart
                    name = list(EXPORTERS.keys())[i]
                    ecfg = exporters_cfg.get(name, {})
                    np = run_exporter(name, ecfg)
                    if np: procs[i] = np
    finally:
        for p in procs:
            with contextlib.suppress(Exception):
                p.terminate()


if __name__ == '__main__':
    main()
