"""FastAPI application entrypoint."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.events.publisher import broadcaster

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # The event broadcaster's publish() is called from sync worker threads
    # and needs the running loop to hand events back to async SSE subscribers.
    broadcaster.bind_loop(asyncio.get_running_loop())
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "REST API for pharmacy staff and managers to capture prescription "
        "orders, track inventory in real time, and automatically fulfil "
        "waiting orders as stock arrives. MySQL is the single source of "
        "truth for every order and inventory decision; nothing here trusts "
        "client-supplied stock figures."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router)
