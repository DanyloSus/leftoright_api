from typing import Optional

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import HTTPBearer as HTTPBearerModel
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBase
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request


class HTTPBearer(HTTPBase):
    def __init__(
        self, *, bearerFormat=None, scheme_name=None, description=None, auto_error=True
    ):
        self.model = HTTPBearerModel(bearerFormat=bearerFormat, description=description)
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        authorization: str = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)

        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )
            return None

        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            return None

        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)
