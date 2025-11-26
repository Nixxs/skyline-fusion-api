from pydantic import BaseModel 


class ClusterRequest(BaseModel):
    max_distance_m: float = 50.0   # distance threshold for assigning to same cluster
    max_yaw_diff_deg: float | None = None
    reset_existing: bool = True    # if True, clears image_classes & image_lookup before recalculating


class ClusterSummary(BaseModel):
    status: str
    clusters_created: int
    images_clustered: int
    unclustered_images: int

