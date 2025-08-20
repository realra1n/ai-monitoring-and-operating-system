from fastapi import APIRouter
from . import routes_auth, routes_health, routes_runs, routes_dashboards, routes_sdk

api_router = APIRouter()

api_router.include_router(routes_health.router, tags=["health"])
api_router.include_router(routes_auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(routes_runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(routes_dashboards.router, prefix="/dashboards", tags=["dashboards"])
api_router.include_router(routes_sdk.router, prefix="/sdk", tags=["sdk"])
