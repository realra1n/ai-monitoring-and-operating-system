from fastapi import APIRouter, Depends
from ...schemas.auth import User
from ...services.auth import get_current_user
from ...core.config import settings

router = APIRouter()


@router.get("")
async def dashboards(current: User = Depends(get_current_user)):
    g = settings.GRAFANA_URL
    return [
        {"id": 1, "name": "System Overview", "url": f"{g}/d/000000012/node-exporter-full"},
        {"id": 2, "name": "K8S Overview", "url": f"{g}/d/k8s/kubernetes"},
    ]
