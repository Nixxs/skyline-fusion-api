# api/utils/exif.py
from typing import Optional, Tuple, Union
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import logging

logger = logging.getLogger(__name__)

NumberLike = Union[float, int]

def _value_to_float(v) -> Optional[float]:
    """
    Handle different EXIF numeric representations:
    - Plain float/int
    - IFDRational (has numerator/denominator)
    - (num, den) tuple
    """
    try:
        # IFDRational-style (Pillow)
        if hasattr(v, "numerator") and hasattr(v, "denominator"):
            num = float(v.numerator)
            den = float(v.denominator) or 1.0
            return num / den

        # (num, den) tuple
        if isinstance(v, (tuple, list)) and len(v) == 2:
            num = float(v[0])
            den = float(v[1]) or 1.0
            return num / den

        # Plain number
        return float(v)
    except Exception:
        return None

def _dms_to_dd(dms, ref) -> Optional[float]:
    """
    Convert GPS coordinates stored as DMS to decimal degrees.
    dms can be:
      - tuple of 3 rationals or IFDRational objects
      - tuple of 3 plain floats (as in your example)
    ref is 'N','S','E','W'.
    """
    if not dms or len(dms) != 3:
        return None

    try:
        deg = _value_to_float(dms[0])
        minutes = _value_to_float(dms[1])
        seconds = _value_to_float(dms[2])

        if deg is None or minutes is None or seconds is None:
            return None

        dd = deg + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ["S", "W"]:
            dd = -dd
        return dd
    except Exception as e:
        print(f"Error converting DMS to DD: {e}")
        return None

def extract_exif_geo(file_path: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Read EXIF from an image file and return (lon, lat, alt_m, yaw_deg).
    Returns (None, None, None, None) if not available.
    """
    try:
        with Image.open(file_path) as img:
            exif = img._getexif()
            if not exif:
                return None, None, None, None

            # Map tag IDs to names
            exif_data = {TAGS.get(tag_id, tag_id): value for tag_id, value in exif.items()}
            gps_info = exif_data.get("GPSInfo")

            if not gps_info:
                return None, None, None, None

            # Convert GPSInfo keys to names
            gps_data = {}
            for key, val in gps_info.items():
                name = GPSTAGS.get(key, key)
                gps_data[name] = val
            
            lat = lon = alt = yaw = None

            # Latitude
            if "GPSLatitude" in gps_data and "GPSLatitudeRef" in gps_data:
                lat = _dms_to_dd(gps_data["GPSLatitude"], gps_data["GPSLatitudeRef"])

            # Longitude
            if "GPSLongitude" in gps_data and "GPSLongitudeRef" in gps_data:
                lon = _dms_to_dd(gps_data["GPSLongitude"], gps_data["GPSLongitudeRef"])
            # Altitude
            if "GPSAltitude" in gps_data:
                try:
                    alt = gps_data["GPSAltitude"]
                except Exception:
                    alt = None

            # TODO:
            # Heading / yaw
            yaw = None

            return lon, lat, alt, yaw

    except Exception:
        # If anything goes wrong, fail soft
        return None, None, None, None
