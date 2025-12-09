from pydantic import BaseModel

class UserIn(BaseModel):
    email: str
    password: str

class HashRequest(BaseModel):
    password: str

class UserOut(BaseModel):
    email: str
    role: str
