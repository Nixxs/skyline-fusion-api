from sqlalchemy.orm import Session
from api.db.models import Image, ImageLookup 
from api.utils.gcp import delete_gcs_image
import logging

logger = logging.getLogger(__name__)

def delete_image_instance(image: Image, db: Session) -> bool:
    """
    Delete a single Image instance, its lookups, adjust image_class.image_count,
    and attempt to delete from GCS.

    Returns:
        bool: True if GCS delete appeared to succeed (or object_name empty),
              False if GCS delete raised an exception.
    """
    image_id = image.image_id
    object_name = image.object_name

    # Delete lookup rows + maintain image_count on classes 
    lookups: list[ImageLookup] = (
        db.query(ImageLookup)
          .filter(ImageLookup.image_id == image_id)
          .all()
    )

    for lk in lookups:
        if lk.image_class is not None:
            ic = lk.image_class
            ic.image_count = max((ic.image_count or 0) - 1, 0)

        db.delete(lk)

    # Delete the image row
    db.delete(image)

    # Try to delete from GCS; do not raise
    gcs_deleted = True
    try:
        if str(object_name):
            delete_gcs_image(str(object_name))
    except Exception as exc:
        gcs_deleted = False
        logger.exception(f"Failed to delete GCS object {object_name}: {exc}")

    return gcs_deleted
