from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.di.exceptions import ErrAlreadyExists, ErrNotFound, ErrPermissionDenied
from app.logging_config import configure_logging, get_logger
from app.middleware import RequestLoggingMiddleware

from .router import api_router

configure_logging()

logger = get_logger(__name__)

app = FastAPI()

app.add_middleware(RequestLoggingMiddleware)
app.include_router(api_router, prefix='/api')


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
