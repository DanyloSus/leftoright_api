from datetime import datetime, timedelta, timezone

import jwt

from app.di.exceptions import ErrPermissionDenied
from app.di.result import Err, Ok


def create_jwt_token(
    secret_key: str, algorithm: str, data: dict, expires: timedelta
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires
    to_encode["exp"] = expire
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def verify_token(token: str, secret_key: str, algorithm: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return Ok(payload)
    except jwt.ExpiredSignatureError:
        return Err(ErrPermissionDenied("Token expired"))
    except jwt.InvalidTokenError:
        return Err(ErrPermissionDenied("Invalid token"))
