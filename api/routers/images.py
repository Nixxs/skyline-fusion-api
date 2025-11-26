import datetime as dt
import logging
import uuid
import zipfile
import os
from typing import cast
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.db.models import Image, ImageClass, ImageLookup
from api.utils.file_handler import save_file
from api.utils.exif import extract_exif_geo
from pathlib import Path
from api.utils.gcp import handle_gcs_image_upload, generate_signed_url
from api.utils.image_classification import cluster_images_by_distance
from api.models.images import GetImageOut, CreateImageOut, CreateImagesOut, BaseImage
from api.models.clusters import ClusterRequest, ClusterSummary

logger = logging.getLogger(__name__)

router = APIRouter()


# -----------------------------
# Route
# -----------------------------

@router.post(
    "/image",
    status_code=201,
    response_model=CreateImageOut,
    tags=["image"],
    summary="Upload a single drone image and extract EXIF metadata",
    description=(
        "Accepts a single drone image as multipart/form-data along with a 'meta' field "
        "containing JSON metadata (name, optional coordinates, etc.).\n\n"
        "The image is saved to disk, EXIF GPS metadata is read (if available), and a row "
        "is created in the `images` table. Explicit values provided in `meta` override "
        "EXIF values; missing values are filled from EXIF when possible."
    ),
)
async def create_image(
    file: UploadFile = File(
        ...,
        description="The drone image file to upload (e.g. JPEG with EXIF GPS data).",
    ),
    db: Session = Depends(get_db),
):
    """
    Upload a single drone image, save it to disk, extract EXIF GPS metadata,
    and create a record in the `images` table.

    **Request format (multipart/form-data)**

    - `file`: binary image file (e.g. JPEG from the drone)

    **Behaviour**

    1. The uploaded file is written under the configured data path (e.g. `data/images/`).
    2. EXIF GPS metadata is read from the saved file.
    3. A row is inserted into `images`.
    4. The created record and file path are returned.
    """

    imported = dt.datetime.now(dt.timezone.utc).isoformat()

    # Save the binary file to disk
    file_path = await save_file(file, subfolder="images")
    logger.info(f"Saved uploaded image to {file_path}")

    # Extract EXIF geo info
    exif_name, exif_lon, exif_lat, exif_alt, exif_yaw, created, geom = extract_exif_geo(file_path)
    logger.info(
        f"EXIF for {file.filename}: "
        f"lon={exif_lon}, lat={exif_lat}, alt={exif_alt}, yaw={exif_yaw}"
    )

    # Decide URL: later this will be a GCS URL; for now we use meta.url or local path
    object_name = handle_gcs_image_upload(file_path)

    image = Image(
        image_id=str(uuid.uuid4()),
        name=exif_name,
        lon=exif_lon,
        lat=exif_lat,
        alt_m=exif_alt,
        yaw_deg=exif_yaw,
        created=created,
        object_name=object_name,
        imported_utc=imported,
        geom=geom
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return CreateImageOut(
        status="ok",
        image=image,
        file_path=file_path,
    )


@router.post(
    "/images",
    status_code=201,
    response_model=CreateImagesOut,
    tags=["image"],
    summary="Upload a zip file of drone images and extract EXIF metadata",
    description=(
        "Accepts a .zip file containing drone image files as multipart/form-data.\n\n"
        "Each image is extracted, saved to disk, EXIF GPS metadata is read (if available), "
        "and a row is created in the `images` table."
    ),
)
async def create_images(
    file: UploadFile = File(
        ...,
        description="A .zip file containing drone image files to upload",
    ),
    db: Session = Depends(get_db),
):
    """
    Upload a zip file containing multiple drone images.

    **Request format (multipart/form-data)**

    - `file`: binary zip file containing the images (e.g. JPEG from the drone)

    **Behaviour**

    1. The uploaded ZIP is written under the configured data path (e.g. `data/images/`).
    2. The ZIP is extracted into a batch folder.
    3. EXIF GPS metadata is read from each extracted image.
    4. A row is inserted into `images` for each valid image.
    5. All created records and file paths are returned.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .zip archive")

    imported = dt.datetime.now(dt.timezone.utc).isoformat()

    # Save the ZIP file to disk (e.g. data/images/myupload.zip)
    zip_path = await save_file(file, subfolder="images")
    logger.info(f"Saved uploaded ZIP to {zip_path}")

    zip_path_obj = Path(zip_path)
    batch_id = uuid.uuid4().hex
    extract_dir = zip_path_obj.parent / f"batch_{batch_id}"
    extract_dir.mkdir(parents=True, exist_ok=True)

    created_images: list[Image] = []
    file_paths: list[str] = []

    try:
        with zipfile.ZipFile(zip_path_obj, "r") as zf:
            for member in zf.namelist():
                # Skip directories
                if member.endswith("/"):
                    continue

                # Only process likely image files
                if not member.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
                    logger.info(f"Skipping non-image file in zip: {member}")
                    continue

                # Extract file
                extracted_path = zf.extract(member, path=extract_dir)
                extracted_path_obj = Path(extracted_path)
                file_paths.append(str(extracted_path_obj))
                logger.info(f"Extracted image {member} to {extracted_path_obj}")

                # Extract EXIF geo info
                exif_name, exif_lon, exif_lat, exif_alt, exif_yaw, created, geom = extract_exif_geo(
                    str(extracted_path_obj)
                )
                logger.info(
                    f"EXIF for {member}: "
                    f"lon={exif_lon}, lat={exif_lat}, alt={exif_alt}, yaw={exif_yaw}"
                )

                # Upload to GCS and store object_name
                object_name = handle_gcs_image_upload(str(extracted_path_obj))

                image = Image(
                    image_id=str(uuid.uuid4()),
                    name=exif_name or extracted_path_obj.name,
                    lon=exif_lon,
                    lat=exif_lat,
                    alt_m=exif_alt,
                    yaw_deg=exif_yaw,
                    created=created,
                    object_name=object_name,
                    imported_utc=imported,
                    geom=geom,
                )

                db.add(image)
                created_images.append(image)

        if not created_images:
            raise HTTPException(status_code=400, detail="No valid image files found in zip archive")

        db.commit()
        for img in created_images:
            db.refresh(img)

        os.rmdir(extract_dir)
        os.remove(zip_path)

        return CreateImagesOut(
            status="ok",
            images=[BaseImage.model_validate(img) for img in created_images],
            file_paths=file_paths,
        )

    except zipfile.BadZipFile:
        logger.exception("Uploaded file is not a valid ZIP")
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid ZIP archive")

@router.get("/image/{image_id}", status_code=200, response_model=GetImageOut)
def get_image_by_id(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Generate a signed URL valid for 1 hour (3600 seconds)
    signed_url = generate_signed_url(str(image.object_name), expires_in_seconds=3600)

    # Use from_attributes + update to avoid manually copying every field
    image_out = BaseImage.model_validate(image)
    image_out = image_out.model_copy(update={"signed_url": signed_url})

    return image_out

@router.post(
    "/images/cluster",
    response_model=ClusterSummary,
    tags=["image"],
    summary="Cluster images into spatial groups",
    description=(
        "Reads all images with a valid lon/lat from the `images` table and groups them into "
        "clusters based on a maximum distance threshold (in meters). "
        "Each cluster becomes an entry in `image_classes`, and `image_lookup` maps images "
        "to their cluster."
    ),
)
def cluster_images_endpoint(
    params: ClusterRequest,
    db: Session = Depends(get_db),
):
    # 1. Load all images with coordinates
    images: list[Image] = (
        db.query(Image)
        .filter(Image.lat.isnot(None))
        .filter(Image.lon.isnot(None))
        .all()
    )

    if not images:
        raise HTTPException(status_code=400, detail="No images with coordinates to cluster")

    total_images = len(images)

    # 2. Optionally clear existing classes & lookups
    if params.reset_existing:
        db.query(ImageLookup).delete()
        db.query(ImageClass).delete()
        db.commit()

    # 3. Cluster in memory
    clusters = cluster_images_by_distance(images, params.max_distance_m, params.max_yaw_diff_deg)

    # 4. Create ImageClass & ImageLookup rows
    now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    clusters_created = 0
    images_clustered = 0

    for cluster in clusters:
        if not cluster:
            continue

        # Compute centroid lat/lon of cluster
        lats = [img.lat for img in cluster if img.lat is not None]
        lons = [img.lon for img in cluster if img.lon is not None]

        if not lats or not lons:
            # Skip cluster with no usable coordinates
            continue

        centroid_lat = cast(float, sum(lats) / len(lats))
        centroid_lon = cast(float, sum(lons) / len(lons))

        # Optionally average alt/yaw too
        alts = [img.alt_m for img in cluster if img.alt_m is not None]
        yaws = [img.yaw_deg for img in cluster if img.yaw_deg is not None]

        avg_alt = sum(alts) / len(alts) if alts else None
        avg_yaw = sum(yaws) / len(yaws) if yaws else None

        class_id = str(uuid.uuid4())
        geom: WKBElement = from_shape(Point(centroid_lon, centroid_lat), srid=4326) 
        image_class = ImageClass(
            class_id=class_id,
            name=f"Cluster {clusters_created + 1}",
            lon=centroid_lon,
            lat=centroid_lat,
            alt_m=avg_alt,
            yaw_deg=avg_yaw,
            image_count=len(cluster),
            updated_utc=now_utc,
            geom=geom 
        )
        db.add(image_class)

        # Create lookup entries
        for img in cluster:
            lookup = ImageLookup(
                image_id=img.image_id,  # note: this is the TEXT id, not numeric PK
                class_id=class_id,
            )
            db.add(lookup)

        clusters_created += 1
        images_clustered += len(cluster)

    db.commit()

    unclustered_images = total_images - images_clustered

    return ClusterSummary(
        status="ok",
        clusters_created=clusters_created,
        images_clustered=images_clustered,
        unclustered_images=unclustered_images,
    )
