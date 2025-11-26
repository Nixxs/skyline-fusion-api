from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.db.models import Image
from api.utils.file_handler import save_file
from api.utils.exif import extract_exif_geo
import datetime as dt
import logging
import uuid
import zipfile
import os
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from api.utils.gcp import handle_gcs_image_upload, generate_signed_url
from typing import List

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
                    "imported_utc": "2025-11-17T07:42:12.788912+00:00"
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
                    },
                ],
                "file_paths": [
                    "D:\\apps\\skyline-fusion-api\\data\\images\\2025-10-07--08-38-21-SG-006919-SCPP-Inspection.jpeg",
                    "D:\\apps\\skyline-fusion-api\\data\\images\\2025-10-07--08-39-01-SG-006920-SCPP-Inspection.jpeg",
                ],
            }
        }
    )

# -----------------------------
# Route
# -----------------------------

@router.post(
    "/image",
    status_code=201,
    response_model=CreateImageOut,
    tags=["image"],
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
    file_path = await save_file(file, subfolder="images")
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


@router.post(
    "/images",
    status_code=201,
    response_model=CreateImagesOut,
    tags=["image"],
    summary="Upload a zip file of drone images and extract EXIF metadata",
    description=(
        "Accepts a .zip file containing drone image files as multipart/form-data.\n\n"
        "Each image is extracted, saved to disk, EXIF GPS metadata is read (if available), "
        "and a row is created in the `images` table."
    ),
)
async def create_images(
    file: UploadFile = File(
        ...,
        description="A .zip file containing drone image files to upload",
    ),
    db: Session = Depends(get_db),
):
    """
    Upload a zip file containing multiple drone images.

    **Request format (multipart/form-data)**

    - `file`: binary zip file containing the images (e.g. JPEG from the drone)

    **Behaviour**

    1. The uploaded ZIP is written under the configured data path (e.g. `data/images/`).
    2. The ZIP is extracted into a batch folder.
    3. EXIF GPS metadata is read from each extracted image.
    4. A row is inserted into `images` for each valid image.
    5. All created records and file paths are returned.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .zip archive")

    imported = dt.datetime.now(dt.timezone.utc).isoformat()

    # Save the ZIP file to disk (e.g. data/images/myupload.zip)
    zip_path = await save_file(file, subfolder="images")
    logger.info(f"Saved uploaded ZIP to {zip_path}")

    zip_path_obj = Path(zip_path)
    batch_id = uuid.uuid4().hex
    extract_dir = zip_path_obj.parent / f"batch_{batch_id}"
    extract_dir.mkdir(parents=True, exist_ok=True)

    created_images: list[Image] = []
    file_paths: list[str] = []

    try:
        with zipfile.ZipFile(zip_path_obj, "r") as zf:
            for member in zf.namelist():
                # Skip directories
                if member.endswith("/"):
                    continue

                # Only process likely image files
                if not member.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
                    logger.info(f"Skipping non-image file in zip: {member}")
                    continue

                # Extract file
                extracted_path = zf.extract(member, path=extract_dir)
                extracted_path_obj = Path(extracted_path)
                file_paths.append(str(extracted_path_obj))
                logger.info(f"Extracted image {member} to {extracted_path_obj}")

                # Extract EXIF geo info
                exif_name, exif_lon, exif_lat, exif_alt, exif_yaw, created, geom = extract_exif_geo(
                    str(extracted_path_obj)
                )
                logger.info(
                    f"EXIF for {member}: "
                    f"lon={exif_lon}, lat={exif_lat}, alt={exif_alt}, yaw={exif_yaw}"
                )

                # Upload to GCS and store object_name
                object_name = handle_gcs_image_upload(str(extracted_path_obj))

                image = Image(
                    image_id=str(uuid.uuid4()),
                    name=exif_name or extracted_path_obj.name,
                    lon=exif_lon,
                    lat=exif_lat,
                    alt_m=exif_alt,
                    yaw_deg=exif_yaw,
                    created=created,
                    object_name=object_name,
                    imported_utc=imported,
                    geom=geom,
                )

                db.add(image)
                created_images.append(image)

        if not created_images:
            raise HTTPException(status_code=400, detail="No valid image files found in zip archive")

        db.commit()
        for img in created_images:
            db.refresh(img)

        os.rmdir(extract_dir)
        os.remove(zip_path)

        return CreateImagesOut(
            status="ok",
            images=[BaseImage.model_validate(img) for img in created_images],
            file_paths=file_paths,
        )

    except zipfile.BadZipFile:
        logger.exception("Uploaded file is not a valid ZIP")
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid ZIP archive")

@router.get("/image/{image_id}", status_code=200, response_model=GetImageOut)
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
