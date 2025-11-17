from pydantic import BaseModel
from typing import Optional

class ImageCreate(BaseModel):
    name: str
    lon: Optional[float] = None
    lat: Optional[float] = None
    alt_m: Optional[float] = None
    yaw_deg: Optional[float] = None
    url: Optional[str] = None  # optional, we may overwrite with file_path/GCS later
