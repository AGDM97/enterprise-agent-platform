from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title = "Enterprise Agent Platform",
    version ="0.1.0",
    description="Cloud-agnostic platform for enterprise AI Systems",
)

app.include_router(router)