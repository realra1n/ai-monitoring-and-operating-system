from typing import Optional, Dict
from pydantic import BaseModel


class SDKStartReq(BaseModel):
    tenant: str
    project: str
    run_name: str
    framework: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class SDKMetricReq(BaseModel):
    run_id: Optional[int] = None
    name: str
    value: float
    step: Optional[int] = None
    epoch: Optional[int] = None
    ts: Optional[int] = None


class SDKLogReq(BaseModel):
    run_id: Optional[int] = None
    level: str = "INFO"
    msg: str
    ts: Optional[int] = None


class SDKTraceReq(BaseModel):
    run_id: Optional[int] = None
    name: str
    duration_ms: int
    ts: Optional[int] = None


class SDKFinishReq(BaseModel):
    run_id: Optional[int] = None
    status: str = "success"
    ts: Optional[int] = None
