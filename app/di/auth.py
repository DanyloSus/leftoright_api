from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials

from app.auth.http import HTTPBearer
from app.auth.token import verify_token
from configs.jwt import JWTConfigDep

bearer_scheme = HTTPBearer()


def _get_user_id(
    config: JWTConfigDep,
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    data, err = verify_token(
        token=token.credentials,
        secret_key=config.SECRET_KEY,
        algorithm=config.ALGORITHM,
    )
    if err:
        raise HTTPException(status_code=401, detail='Invalid token')

    sub = data.get('sub')
    if sub is None:
        raise HTTPException(status_code=401, detail='Invalid token')

    return int(sub)


UserIdDep = Annotated[int, Depends(_get_user_id)]
