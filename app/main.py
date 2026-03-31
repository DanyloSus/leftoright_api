from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.di.exceptions import ErrAlreadyExists, ErrNotFound, ErrPermissionDenied
from app.di.limiter import limiter
from app.logging_config import configure_logging, get_logger
from app.middleware import RequestLoggingMiddleware
from configs.cors import get_cors_config
from configs.redis_client import redis_client
from configs.session import engine

from .router import api_router

configure_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("startup")
    yield
    logger.info("shutdown_started")
    await engine.dispose()
    await redis_client.aclose()
    logger.info("shutdown_complete")


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter

_cors = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=_cors.ALLOW_METHODS,
    allow_headers=_cors.ALLOW_HEADERS,
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(api_router, prefix='/api')


@app.exception_handler(RateLimitExceeded)
async def _(req: Request, err: RateLimitExceeded):
    return JSONResponse(status_code=429, content={'detail': str(err)})


@app.exception_handler(ErrAlreadyExists)
async def _(req: Request, err: ErrAlreadyExists):
    logger.warning("conflict_error", detail=err.message)
    return JSONResponse(status_code=409, content={'detail': err.message})


@app.exception_handler(ErrNotFound)
async def _(req: Request, err: ErrNotFound):
    logger.warning("not_found_error", detail=err.message)
    return JSONResponse(status_code=404, content={'detail': err.message})


@app.exception_handler(ErrPermissionDenied)
async def _(req: Request, err: ErrPermissionDenied):
    logger.warning("permission_denied_error", detail=err.message)
    return JSONResponse(status_code=403, content={'detail': err.message})
