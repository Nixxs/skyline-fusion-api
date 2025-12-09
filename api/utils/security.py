import logging
import datetime as dt
from typing import Annotated
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, ExpiredSignatureError, JWTError
from api.config import config
from api.models.auth import UserOut

logger = logging.getLogger("api")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"

    local, domain = email.split("@", 1)
    if not domain:
        return "***"

    parts = domain.split(".")
    if len(parts) < 2:
        # no real tld – mask simply
        l_shown = local[:3]
        l_masked = "*" * max(len(local) - 3, 0)
        d_shown = domain[:3]
        d_masked = "*" * max(len(domain) - 3, 0)
        return f"{l_shown}{l_masked}@{d_shown}{d_masked}"

    tld = parts[-1]                 # "com"
    domain_name = ".".join(parts[:-1])  # "example" or "example.co"

    l_shown = local[:3]
    l_masked = "*" * max(len(local) - 3, 0)

    d_shown = domain_name[:3]
    d_masked = "*" * max(len(domain_name) - 3, 0)

    return f"{l_shown}{l_masked}@{d_shown}{d_masked}.{tld}"

def create_access_token(email:str, role:str) -> str:
    logger.info(f"creating token for: {mask_email(email)}")
    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30)

    jwt_data = {
        "email": email,
        "role": role,
        "exp": expire
    }

    encoded_jwt = jwt.encode(jwt_data, config.JWT_SECRET, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserOut:
    try:
        payload = jwt.decode(token, key=config.JWT_SECRET, algorithms=[ALGORITHM])
        email = payload.get("email")
        role = payload.get("role")
        logger.info(f"successfully authenticated user {mask_email(str(email))}")
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401,
            detail="token has expired",
            headers={"WWW-AUthenticate":"Bearer"}
        ) from e
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="could not validate credentials",
            headers={"WWW-AUthenticate":"Bearer"}
        )

    user = UserOut(email=config.ADMIN_USER_EMAIL, role=str(role))

    return user
