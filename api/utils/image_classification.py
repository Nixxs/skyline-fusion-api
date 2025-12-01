import math
from typing import Any


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Returns distance in meters between two WGS84 points.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def yaw_diff_deg(a: float, b: float) -> float:
    """
    Smallest angular difference between two headings in degrees (0–180).
    """
    diff = abs(a - b) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff

def cluster_images_by_distance(
    images: list[Any],
    max_distance_m: float,
    max_yaw_diff_deg: float | None = None,
) -> list[list[Any]]:
    """
    Simple greedy clustering with optional yaw constraint:
    - Take first unassigned image -> new cluster center.
    - Assign any other images within max_distance_m (and yaw diff if given).
    - Repeat until all images are assigned.
    """
    unassigned: set[Any] = set(images)
    clusters: list[list[Any]] = []

    while unassigned:
        seed = unassigned.pop()
        cluster = [seed]

        seed_lat = seed.lat
        seed_lon = seed.lon
        seed_yaw = getattr(seed, "yaw_deg", None)
        seed_image_type = seed.image_type

        to_add: list[Any] = []
        for img in list(unassigned):
            # Must have coordinates
            if img.lat is None or img.lon is None:
                continue
            if seed_lat is None or seed_lon is None:
                continue

            d = haversine_m(seed_lat, seed_lon, img.lat, img.lon)
            if d > max_distance_m:
                continue

            # Optional yaw filter
            if max_yaw_diff_deg is not None:
                img_yaw = getattr(img, "yaw_deg", None)
                if seed_yaw is None or img_yaw is None:
                    # if you *require* yaw for yaw-based clustering, skip those without yaw:
                    continue

                if yaw_diff_deg(seed_yaw, img_yaw) > max_yaw_diff_deg:
                    continue

            if img.image_type != seed_image_type:
                continue

            to_add.append(img)

        for img in to_add:
            unassigned.remove(img)
            cluster.append(img)

        clusters.append(cluster)

    return clusters
