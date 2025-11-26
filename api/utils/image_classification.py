
import math
from api.db.models import Image
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


def cluster_images_by_distance(
    images: list[Image],
    max_distance_m: float,
) -> list[list[Image]]:
    """
    Very simple greedy clustering:
    - Take first unassigned image -> new cluster center.
    - Assign any other images within max_distance_m to that cluster.
    - Repeat until all images are assigned.

    Returns a list of clusters, where each cluster is a list[Image].
    """
    unassigned = set(images)
    clusters: list[list[Any]] = []

    while unassigned:
        # Start new cluster with an arbitrary image
        seed = unassigned.pop()
        cluster = [seed]

        # We will compare everything to seed's location (simple but usually ok)
        seed_lat = seed.lat
        seed_lon = seed.lon

        # Collect images within threshold
        to_add = []
        for img in list(unassigned):
            if img.lat is None or img.lon is None:
                continue
            if seed_lat is None or seed_lon is None:
                continue

            d = haversine_m(seed_lat, seed_lon, img.lat, img.lon) # type: ignore
            if d <= max_distance_m:
                to_add.append(img)

        # Move them from unassigned -> cluster
        for img in to_add:
            unassigned.remove(img)
            cluster.append(img)

        clusters.append(cluster)

    return clusters
