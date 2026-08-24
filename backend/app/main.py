import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.core.config import get_frontend_origins, get_settings
from app.core.database import Base, engine
from app.core.exceptions import AppException, app_exception_handler
from app.models import *  # noqa: F403
from app.routers.ai import router as ai_router
from app.routers.orders import router as orders_router
from app.routers.support import router as support_router
from app.routers.tickets import router as tickets_router

settings = get_settings()

app = FastAPI(title="ParcelPilot API", version="0.1.0")
app.add_exception_handler(AppException, app_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = f"req_{uuid.uuid4().hex[:16]}"
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Response-Time-Ms"] = str(round((time.perf_counter() - start) * 1000, 2))
    return response


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "ParcelPilot API",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(support_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
