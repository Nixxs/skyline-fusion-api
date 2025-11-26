from pydantic import BaseModel 


class ClusterRequest(BaseModel):
    max_distance_m: float = 50.0   # distance threshold for assigning to same cluster
    reset_existing: bool = True    # if True, clears image_classes & image_lookup before recalculating


class ClusterSummary(BaseModel):
    status: str
    clusters_created: int
    images_clustered: int
    unclustered_images: int

