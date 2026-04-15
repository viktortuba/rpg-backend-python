from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings

bearer_scheme = HTTPBearer()


@dataclass
class TokenData:
    user_id: str
    username: str
    role: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenData:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return TokenData(
            user_id=payload["sub"],
            username=payload["username"],
            role=payload["role"],
        )
    except (JWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def require_game_master(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    if current_user.role != "GameMaster":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="GameMaster role required")
    return current_user
