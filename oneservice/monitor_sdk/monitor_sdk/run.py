import time
import json
import os
import contextlib
import requests
from typing import Dict, Any, Optional

class OneServiceRun:
    def __init__(self, base_url: str, api_token: str, tenant: str, project: str, run_name: str, framework: str = "pytorch", tags: Optional[Dict[str, Any]] = None):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.tenant = tenant
        self.project = project
        self.run_name = run_name
        self.framework = framework
        self.tags = tags or {}
        self.run_id = int(time.time())

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

    def log_metric(self, name: str, value: float, step: Optional[int] = None, epoch: Optional[int] = None):
        payload = {"name": name, "value": value, "step": step, "epoch": epoch, "ts": int(time.time())}
        try:
            requests.post(f"{self.base_url}/api/sdk/metric", headers=self._headers(), data=json.dumps(payload), timeout=3)
        except Exception:
            pass

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None, epoch: Optional[int] = None):
        for k, v in metrics.items():
            self.log_metric(k, v, step=step, epoch=epoch)

    def log_text(self, text: str, level: str = "INFO"):
        payload = {"level": level, "msg": text, "ts": int(time.time())}
        try:
            requests.post(f"{self.base_url}/api/sdk/log", headers=self._headers(), data=json.dumps(payload), timeout=3)
        except Exception:
            pass

    @contextlib.contextmanager
    def span(self, name: str):
        start = time.time()
        yield
        dur = time.time() - start
        payload = {"name": name, "duration_ms": int(dur*1000), "ts": int(time.time())}
        try:
            requests.post(f"{self.base_url}/api/sdk/trace", headers=self._headers(), data=json.dumps(payload), timeout=3)
        except Exception:
            pass

    def upload_artifact(self, path: str):
        url = f"{self.base_url}/api/sdk/artifact"
        fname = os.path.basename(path)
        files = {"file": (fname, open(path, 'rb'))}
        headers = {"Authorization": f"Bearer {self.api_token}"}
        try:
            requests.post(url, headers=headers, files=files, timeout=10)
        except Exception:
            pass

    def finish(self, status: str = "success"):
        payload = {"status": status, "ts": int(time.time())}
        try:
            requests.post(f"{self.base_url}/api/sdk/finish", headers=self._headers(), data=json.dumps(payload), timeout=3)
        except Exception:
            pass
