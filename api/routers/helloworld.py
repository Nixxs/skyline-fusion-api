import logging

from fastapi import APIRouter, Depends

from api.models.helloworld import HelloWorld
from api.utils.security import get_current_user
from api.models.auth import UserOut
from typing import Annotated

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/helloworld", response_model=HelloWorld, status_code=200)
async def get_hello_world(current_user: Annotated[UserOut, Depends(get_current_user)]):
    return {"message": f"Hello {current_user.email} from FastAPI!"}

