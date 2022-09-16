import json
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils import (
    ALGORITHM,
    JWT_SECRET_KEY
)
from jose import jwt
from pydantic import ValidationError
from schemas import TokenPayload, SystemUser

reusable_oauth = OAuth2PasswordBearer(
    tokenUrl="/kirjaudu",
    scheme_name="JWT"
)


async def get_current_user(token: str = Depends(reusable_oauth)) -> SystemUser:
    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except(jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    u = json.load(open('users.json', encoding='utf-8'))
    user = None
    if u["username"] == token_data.sub:
        user = u

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    return SystemUser(**user)