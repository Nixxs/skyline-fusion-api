import logging

from fastapi import APIRouter

from api.models.helloworld import HelloWorld


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/helloworld", response_model=HelloWorld, status_code=200)
async def get_hello_world():
    return {"message": "Hello World"}

