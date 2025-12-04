# api/utils/exif.py
from typing import Optional, Tuple
import logging
from exiftool import ExifToolHelper
from datetime import datetime
from api.config import config
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from geoalchemy2 import WKBElement
from api.utils.fov import compute_hv_fov

logger = logging.getLogger(__name__)

def extract_exif_geo(file_path: str) -> Tuple[
        Optional[str], 
        Optional[float], 
        Optional[float], 
        Optional[float], 
        Optional[float], 
        Optional[datetime], 
        Optional[WKBElement], 
        Optional[str], 
        Optional[float],
        Optional[float],
        Optional[float],
        Optional[float],
        Optional[float],
        Optional[float]
    ]:
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
            yaw:float  = metadata.get("XMP:FlightYawDegree")
            created:datetime = datetime.strptime(metadata.get("EXIF:CreateDate"), "%Y:%m:%d %H:%M:%S")
            geom:WKBElement = from_shape(Point(lon, lat), srid=4326)
            image_type:str = metadata.get("EXIF:XPKeywords")
            pitch:float = metadata.get("XMP:GimbalPitchDegree")

            width_px:int = metadata.get("EXIF:ExifImageWidth")
            height_px:int = metadata.get("EXIF:ExifImageHeight")
            cfov:float = metadata.get("Composite:FOV")

            hfov, vfov = compute_hv_fov(cfov, width_px, height_px)

            target_range = metadata.get("XMP:LRFTargetDistance")
            target_lon = metadata.get("XMP:LRFTargetLon")
            target_lat = metadata.get("XMP:LRFTargetLat")

            return name, lon, lat, alt, yaw, created, geom, image_type, pitch, hfov, vfov, target_range, target_lon, target_lat

    except Exception as e:
        # If anything goes wrong, fail soft
        logger.warning(f"Failed to extract EXIF from {file_path}: {e}")
        return None, None, None, None, None, None, None, None, None, None, None, None, None, None
