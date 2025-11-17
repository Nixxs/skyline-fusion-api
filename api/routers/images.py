from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.db.models import Image
from api.models.image import ImageCreate
from api.utils.file_handler import save_image_file
from api.utils.exif import extract_exif_geo
import datetime as dt
import logging
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

router = APIRouter()


# -----------------------------
# Pydantic response models
# -----------------------------

class ImageOut(BaseModel):
    image_id: int
    name: str
    lon: float | None = None
    lat: float | None = None
    alt_m: float | None = None
    yaw_deg: float | None = None
    url: str
    class_id: int | None = None
    imported_utc: str

    # Needed so FastAPI can serialize from SQLAlchemy model instances
    model_config = ConfigDict(from_attributes=True)

class CreateImageOut(BaseModel):
    status: str
    image: ImageOut
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
    meta: str = Form(
        ...,
        description=(
            "JSON string containing image metadata. Example:\n"
            '{\n'
            '  "name": "2025-08-27--12-55-33-SG-006614-SCPP-Inspection.jpeg",\n'
            '  "lon": null,\n'
            '  "lat": null,\n'
            '  "alt_m": null,\n'
            '  "yaw_deg": null,\n'
            '  "url": null\n'
            '}'
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Upload a single drone image, save it to disk, extract EXIF GPS metadata,
    and create a record in the `images` table.

    **Request format (multipart/form-data)**

    - `file`: binary image file (e.g. JPEG from the drone)
    - `meta`: JSON string with fields:
        - `name` (str): logical image name (usually original filename)
        - `lon` (float, optional): longitude override; if null, EXIF is used
        - `lat` (float, optional): latitude override; if null, EXIF is used
        - `alt_m` (float, optional): altitude override; if null, EXIF is used
        - `yaw_deg` (float, optional): yaw/heading override; if null, EXIF (if present) is used
        - `url` (str, optional): external URL; if null, the local file path is used

    **Behaviour**

    1. The uploaded file is written under the configured data path (e.g. `data/images/`).
    2. EXIF GPS metadata is read from the saved file.
    3. Explicit values from `meta` override EXIF values where provided.
    4. A row is inserted into `images`.
    5. The created record and file path are returned.
    """
    # Parse meta JSON into Pydantic model
    try:
        image_meta = ImageCreate.model_validate_json(meta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid meta JSON: {e}")

    imported = dt.datetime.now(dt.timezone.utc).isoformat()

    # Save the binary file to disk
    file_path = await save_image_file(file, subfolder="images")
    logger.info(f"Saved uploaded image to {file_path}")

    # Extract EXIF geo info
    exif_lon, exif_lat, exif_alt, exif_yaw = extract_exif_geo(file_path)
    logger.info(
        f"EXIF for {file.filename}: "
        f"lon={exif_lon}, lat={exif_lat}, alt={exif_alt}, yaw={exif_yaw}"
    )

    # Merge: explicit meta wins, EXIF fills gaps
    lon = image_meta.lon if image_meta.lon is not None else exif_lon
    lat = image_meta.lat if image_meta.lat is not None else exif_lat
    alt_m = image_meta.alt_m if image_meta.alt_m is not None else exif_alt
    yaw_deg = image_meta.yaw_deg if image_meta.yaw_deg is not None else exif_yaw

    # Decide URL: later this will be a GCS URL; for now we use meta.url or local path
    final_url = image_meta.url or file_path

    image = Image(
        name=image_meta.name,
        lon=lon,
        lat=lat,
        alt_m=alt_m,
        yaw_deg=yaw_deg,
        url=final_url,
        class_id=None,
        imported_utc=imported,
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return CreateImageOut(
        status="ok",
        image=image,
        file_path=file_path,
    )

@router.get("/images/{image_id}", status_code=200)
def get_image_by_id(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image
