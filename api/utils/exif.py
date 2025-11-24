# api/utils/exif.py
from typing import Optional, Tuple
import logging
from exiftool import ExifToolHelper
from datetime import datetime
from api.config import config
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from geoalchemy2 import Geometry, WKBElement

logger = logging.getLogger(__name__)

def extract_exif_geo(file_path: str) -> Tuple[Optional[str], Optional[float], Optional[float], Optional[float], Optional[float], Optional[datetime], Optional[WKBElement]]:
    """
    Read EXIF from an image file and return (name, lon, lat, alt_m, yaw_deg, created).
    Returns (None,None, None, None, None, None) if not available.
    """
    try:
        with ExifToolHelper(executable=config.EXIF_TOOL_PATH) as et:
            metadata = et.get_metadata(file_path)[0]

            name:str = metadata.get("File:FileName")
            lat:float = -metadata.get("EXIF:GPSLatitude")
            lon:float = metadata.get("EXIF:GPSLongitude")
            alt:float = metadata.get("EXIF:GPSAltitude")
            yaw:float  = metadata.get("XMP:GimbalYawDegree")
            created:datetime = datetime.strptime(metadata.get("EXIF:CreateDate"), "%Y:%m:%d %H:%M:%S")
            geom:WKBElement = from_shape(Point(lon, lat), srid=4326)

            return name, lon, lat, alt, yaw, created, geom

    except Exception as e:
        # If anything goes wrong, fail soft
        logger.warning(f"Failed to extract EXIF from {file_path}: {e}")
        return None, None, None, None, None, None, None
