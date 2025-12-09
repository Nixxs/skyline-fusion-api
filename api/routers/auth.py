import logging
from fastapi import APIRouter, HTTPException 
from api.models.auth import UserIn, HashRequest
from api.utils.security import mask_email, create_access_token
from passlib.context import CryptContext
from api.config import config

router = APIRouter() 
logger = logging.getLogger("api")

pwd_context = CryptContext(schemes=["bcrypt"])

@router.post("/login", status_code=200, include_in_schema=False)
async def login(user: UserIn):
    masked_email = mask_email(user.email)
    plain_password = user.password
    hashed_password = config.ADMIN_USER_PASSWORD_HASH

    verified = pwd_context.verify(plain_password, hashed_password)

    if verified and (user.email.lower() == config.ADMIN_USER_EMAIL.lower()):
        logger.info(f"user: {masked_email} verified")

        token = create_access_token(user.email, "admin")
    else:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-AUthenticate": "Bearer"}
        )

    return{
        "access_token":token,
        "token_type":"bearer"
    }



@router.post("/hash", status_code=200, include_in_schema=False)
async def hash(hashRequest: HashRequest):
    logger.info(hashRequest.password)
    return {
        "hashed": pwd_context.hash(hashRequest.password)
    }
