from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.db.models import Image
from api.models.image import ImageCreate
import datetime

router = APIRouter(prefix="/images", tags=["Images"])

@router.post("/", status_code=201)
def create_image(payload: ImageCreate, db: Session = Depends(get_db)):
    imported = datetime.datetime.now(datetime.timezone.utc).isoformat()

    image = Image(
        name=payload.name,
        lon=payload.lon,
        lat=payload.lat,
        alt_m=payload.alt_m,
        yaw_deg=payload.yaw_deg,
        url=payload.url,
        class_id=None,
        imported_utc=imported,
    )

    db.add(image)
    db.commit()
    db.refresh(image)  # reload with assigned ID

    return {"status": "ok", "image": image}
