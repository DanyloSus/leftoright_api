from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.exceptions import ErrAlreadyExists, ErrNotFound, ErrPermissionDenied

from .router import api_router

app = FastAPI()

app.include_router(api_router, prefix='/api')


@app.exception_handler(ErrAlreadyExists)
async def _(req, err: ErrAlreadyExists):
    return JSONResponse(status_code=409, content={'detail': err.message})


@app.exception_handler(ErrNotFound)
async def _(req, err: ErrNotFound):
    return JSONResponse(status_code=404, content={'detail': err.message})


@app.exception_handler(ErrPermissionDenied)
async def _(req, err: ErrPermissionDenied):
    return JSONResponse(status_code=403, content={'detail': err.message})
