from pydantic import BaseModel, ConfigDict
from typing import List
import datetime as dt

# -----------------------------
# Pydantic response models
# -----------------------------

class GetImageOut(BaseModel):
    image_id: str
    name: str
    lon: float | None = None
    lat: float | None = None
    alt_m: float | None = None
    yaw_deg: float | None = None
    created: dt.datetime | None = None
    signed_url: str
    object_name: str
    imported_utc: str
    image_type: str
    pitch: float | None = None
    hfov: float | None = None
    vfov: float | None = None
    target_range: float | None = None
    target_lon: float | None = None
    target_lat: float | None = None
    category: str

    # Needed so FastAPI can serialize from SQLAlchemy model instances
    model_config = ConfigDict(from_attributes=True)

class BaseImage(BaseModel):
    image_id: str
    name: str
    lon: float | None = None
    lat: float | None = None
    alt_m: float | None = None
    yaw_deg: float | None = None
    created: dt.datetime | None = None
    object_name: str
    imported_utc: str
    image_type: str
    pitch: float | None = None
    hfov: float | None = None
    vfov: float | None = None
    target_range: float | None = None
    target_lon: float | None = None
    target_lat: float | None = None
    category: str

    # Needed so FastAPI can serialize from SQLAlchemy model instances
    model_config = ConfigDict(from_attributes=True)

class CreateImageOut(BaseModel):
    status: str
    image: BaseImage
    file_path: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "image": {
                    "image_id": 24,
                    "name": "2025-08-27--12-55-33-SG-006614-SCPP-Inspection.jpeg",
                    "lon": 139.49234083333332,
                    "lat": -30.151920194444443,
                    "alt_m": 181.128,
                    "yaw_deg": 190.0,
                    "imported_utc": "2025-11-17T07:42:12.788912+00:00",
                    "image_type": "standard",
                    "pitch": 34.22,
                    "hfov": 120.45,
                    "vfov": 90.1
                },
                "file_path": "D:\\apps\\skyline-fusion-api\\data\\images\\2025-08-27--12-55-33-SG-006614-SCPP-Inspection.jpeg"
            }
        }
    )

class CreateImagesOut(BaseModel):
    status: str
    images: List[BaseImage]
    file_paths: List[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "images": [
                    {
                        "image_id": "63fbcd80-8e84-4c2d-b3c1-d0155329c638",
                        "name": "2025-10-07--08-38-21-SG-006919-SCPP-Inspection.jpeg",
                        "lon": 139.548454833333,
                        "lat": -30.1478478055556,
                        "alt_m": 174.738,
                        "yaw_deg": -13.1,
                        "created": "2025-10-07T08:38:21",
                        "object_name": "images/2025-10-07--08-38-21-SG-006919-SCPP-Inspection.jpeg",
                        "imported_utc": "2025-11-24T14:20:20.290730+00:00",
                        "image_type": "standard"
                    },
                    {
                        "image_id": "5f4744a8-6a5b-4a70-9e28-9d0d4a57af11",
                        "name": "2025-10-07--08-39-01-SG-006920-SCPP-Inspection.jpeg",
                        "lon": 139.5485,
                        "lat": -30.1479,
                        "alt_m": 175.0,
                        "yaw_deg": -10.0,
                        "created": "2025-10-07T08:39:01",
                        "object_name": "images/2025-10-07--08-39-01-SG-006920-SCPP-Inspection.jpeg",
                        "imported_utc": "2025-11-24T14:25:10.000000+00:00",
                        "image_type": "standard"
                    },
                ],
                "file_paths": [
                    "D:\\apps\\skyline-fusion-api\\data\\images\\2025-10-07--08-38-21-SG-006919-SCPP-Inspection.jpeg",
                    "D:\\apps\\skyline-fusion-api\\data\\images\\2025-10-07--08-39-01-SG-006920-SCPP-Inspection.jpeg",
                ],
            }
        }
    )

class DeleteImagesRequest(BaseModel):
    image_ids: List[str]

class ImageListItem(BaseModel):
    image_id: str
    name: str
    lon: float | None = None
    lat: float | None = None
    alt_m: float | None = None
    yaw_deg: float | None = None
    created: dt.datetime | None = None
    imported_utc: str
    image_type: str | None = None
    hfov: float | None = None
    vfov: float | None = None
    pitch: float | None = None
    target_range: float | None = None
    target_lon: float | None = None
    target_lat: float | None = None
    category: str

    # So FastAPI can serialize directly from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)


class ImageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ImageListItem]

class ImageIdsIn(BaseModel):
    image_ids: List[str]

class ImageSignedUrlOut(BaseModel):
    image_id: str
    signed_url: str
    name: str
