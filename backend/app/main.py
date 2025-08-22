from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.router import api_router


app = FastAPI(title="OneService Backend", openapi_url="/api/openapi.json", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount versioned API under /api to keep existing paths working
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"name": "OneService Backend", "docs": "/api/docs"}
