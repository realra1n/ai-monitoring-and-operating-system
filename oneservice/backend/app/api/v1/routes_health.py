from fastapi import APIRouter
import time

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "ts": int(time.time())}
