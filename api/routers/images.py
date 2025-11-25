from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.db.models import Image
from api.utils.file_handler import save_image_file
from api.utils.exif import extract_exif_geo
import datetime as dt
import logging
import uuid
from pydantic import BaseModel, ConfigDict
from api.utils.gcp import handle_gcs_image_upload, generate_signed_url

logger = logging.getLogger(__name__)

router = APIRouter()


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
                    "url": "D:\\apps\\skyline-fusion-api\\data\\images\\2025-08-27--12-55-33-SG-006614-SCPP-Inspection.jpeg",
                    "class_id": 3,
                    "imported_utc": "2025-11-17T07:42:12.788912+00:00"
                },
                "file_path": "D:\\apps\\skyline-fusion-api\\data\\images\\2025-08-27--12-55-33-SG-006614-SCPP-Inspection.jpeg"
            }
        }
    )

# -----------------------------
# Route
# -----------------------------

@router.post(
    "/images",
    status_code=201,
    response_model=CreateImageOut,
    tags=["images"],
    summary="Upload a single drone image and extract EXIF metadata",
    description=(
        "Accepts a single drone image as multipart/form-data along with a 'meta' field "
        "containing JSON metadata (name, optional coordinates, etc.).\n\n"
        "The image is saved to disk, EXIF GPS metadata is read (if available), and a row "
        "is created in the `images` table. Explicit values provided in `meta` override "
        "EXIF values; missing values are filled from EXIF when possible."
    ),
)
async def create_image(
    file: UploadFile = File(
        ...,
        description="The drone image file to upload (e.g. JPEG with EXIF GPS data).",
    ),
    db: Session = Depends(get_db),
):
    """
    Upload a single drone image, save it to disk, extract EXIF GPS metadata,
    and create a record in the `images` table.

    **Request format (multipart/form-data)**

    - `file`: binary image file (e.g. JPEG from the drone)

    **Behaviour**

    1. The uploaded file is written under the configured data path (e.g. `data/images/`).
    2. EXIF GPS metadata is read from the saved file.
    3. A row is inserted into `images`.
    4. The created record and file path are returned.
    """

    imported = dt.datetime.now(dt.timezone.utc).isoformat()

    # Save the binary file to disk
    file_path = await save_image_file(file, subfolder="images")
    logger.info(f"Saved uploaded image to {file_path}")

    # Extract EXIF geo info
    exif_name, exif_lon, exif_lat, exif_alt, exif_yaw, created, geom = extract_exif_geo(file_path)
    logger.info(
        f"EXIF for {file.filename}: "
        f"lon={exif_lon}, lat={exif_lat}, alt={exif_alt}, yaw={exif_yaw}"
    )

    # Decide URL: later this will be a GCS URL; for now we use meta.url or local path
    object_name = handle_gcs_image_upload(file_path)

    image = Image(
        image_id=str(uuid.uuid4()),
        name=exif_name,
        lon=exif_lon,
        lat=exif_lat,
        alt_m=exif_alt,
        yaw_deg=exif_yaw,
        created=created,
        object_name=object_name,
        imported_utc=imported,
        geom=geom
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return CreateImageOut(
        status="ok",
        image=image,
        file_path=file_path,
    )

@router.get("/images/{image_id}", status_code=200, response_model=GetImageOut)
def get_image_by_id(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Generate a signed URL valid for 1 hour (3600 seconds)
    signed_url = generate_signed_url(str(image.object_name), expires_in_seconds=3600)

    # Use from_attributes + update to avoid manually copying every field
    image_out = BaseImage.model_validate(image)
    image_out = image_out.model_copy(update={"signed_url": signed_url})

    return image_out
