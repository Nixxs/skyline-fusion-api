from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.db.models import Image
from api.models.image import ImageCreate
from api.utils.file_handler import save_image_file
from api.utils.exif import extract_exif_geo
import datetime as dt
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/images", 
    status_code=201,
    tags=["images"],
)
async def create_image(
    file: UploadFile = File(...),
    meta: str = Form(...),   # JSON string containing metadata
    db: Session = Depends(get_db),
):
    # Parse meta JSON into Pydantic model
    try:
        image_meta = ImageCreate.model_validate_json(meta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid meta JSON: {e}")

    imported = dt.datetime.now(dt.timezone.utc).isoformat()

    # Save the binary file somewhere on disk (for now local; later GCS)
    file_path = await save_image_file(file, subfolder="images")
    
    # Extract EXIF geo from saved file
    exif_lon, exif_lat, exif_alt, exif_yaw = extract_exif_geo(file_path)

    # Merge: explicit meta wins, EXIF fills gaps
    lon = image_meta.lon if image_meta.lon is not None else exif_lon
    lat = image_meta.lat if image_meta.lat is not None else exif_lat
    alt_m = image_meta.alt_m if image_meta.alt_m is not None else exif_alt
    yaw_deg = image_meta.yaw_deg if image_meta.yaw_deg is not None else exif_yaw

    # For now, path on disk or meta.url if provided.
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

    return {
        "status": "ok",
        "image": image,
        "file_path": file_path,  # useful for debugging; can be removed later
    }


@router.get("/{image_id}", status_code=200)
def get_image_by_id(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image
