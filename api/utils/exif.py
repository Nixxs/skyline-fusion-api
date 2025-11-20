# api/utils/exif.py
from typing import Optional, Tuple
import logging
from exiftool import ExifToolHelper
from datetime import datetime
from api.config import config

logger = logging.getLogger(__name__)

def extract_exif_geo(file_path: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Read EXIF from an image file and return (name, lon, lat, alt_m, yaw_deg, created).
    Returns (None,None, None, None, None, None) if not available.
    """
    try:
        with ExifToolHelper(executable=config.EXIF_TOOL_PATH) as et:
            metadata = et.get_metadata(file_path)[0]

            name = metadata.get("File:FileName")
            lat = metadata.get("EXIF:GPSLatitude")
            lon = metadata.get("EXIF:GPSLongitude")
            alt = metadata.get("EXIF:GPSAltitude")
            yaw = metadata.get("XMP:GimbalYawDegree")
            created = datetime.strptime(metadata.get("EXIF:CreateDate"), "%Y:%m:%d %H:%M:%S")

            return name, lon, lat, alt, yaw, created

    except Exception as e:
        # If anything goes wrong, fail soft
        logger.warning(f"Failed to extract EXIF from {file_path}: {e}")
        return None, None, None, None, None