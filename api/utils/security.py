import logging
import datetime as dt
from jose import jwt, ExpiredSignatureError, JWTError
from api.config import config

logger = logging.getLogger("api")
ALGORITHM = "HS256"

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
