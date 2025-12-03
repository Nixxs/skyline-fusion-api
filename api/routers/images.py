import datetime as dt
import logging
import uuid
import zipfile
import os
import shutil
from typing import cast, List
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
from api.utils.gcp import handle_gcs_image_upload, generate_signed_url, delete_gcs_image
from api.utils.image_classification import cluster_images_by_distance
from api.models.images import GetImageOut, CreateImageOut, CreateImagesOut, BaseImage
from api.models.clusters import ClusterRequest, ClusterSummary, ClusterOut

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
    exif_name, exif_lon, exif_lat, exif_alt, exif_yaw, created, geom, image_type, pitch, hfov, vfov = extract_exif_geo(file_path)
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
        geom=geom,
        image_type=image_type,
        pitch=pitch,
        hfov=hfov,
        vfov=vfov
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

    IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")

    try:
        # 1) Extract everything first
        with zipfile.ZipFile(zip_path_obj, "r") as zf:
            zf.extractall(extract_dir)
            logger.info(f"Extracted ZIP to {extract_dir}")

        # 2) Walk the extracted tree recursively
        for root, dirs, files in os.walk(extract_dir):
            for filename in files:
                if not filename.lower().endswith(IMAGE_EXTENSIONS):
                    rel = Path(root, filename).relative_to(extract_dir)
                    logger.info(f"Skipping non-image file in zip tree: {rel}")
                    continue

                extracted_path_obj = Path(root) / filename
                rel_path = extracted_path_obj.relative_to(extract_dir)
                file_paths.append(str(extracted_path_obj))
                logger.info(f"Found image {rel_path} at {extracted_path_obj}")

                # Extract EXIF geo info
                (
                    exif_name,
                    exif_lon,
                    exif_lat,
                    exif_alt,
                    exif_yaw,
                    created,
                    geom,
                    image_type,
                    pitch,
                    hfov,
                    vfov,
                ) = extract_exif_geo(str(extracted_path_obj))

                logger.info(
                    f"EXIF for {rel_path}: "
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
                    image_type=image_type,
                    pitch=pitch,
                    hfov=hfov,
                    vfov=vfov,
                )

                db.add(image)
                created_images.append(image)

        if not created_images:
            raise HTTPException(status_code=400, detail="No valid image files found in zip archive")

        db.commit()
        for img in created_images:
            db.refresh(img)

        # Clean up extracted tree + zip
        shutil.rmtree(extract_dir, ignore_errors=True)
        os.remove(zip_path)

        return CreateImagesOut(
            status="ok",
            images=[BaseImage.model_validate(img) for img in created_images],
            file_paths=file_paths,
        )

    except zipfile.BadZipFile:
        logger.exception("Uploaded file is not a valid ZIP")
        # best-effort cleanup
        shutil.rmtree(extract_dir, ignore_errors=True)
        if zip_path_obj.exists():
            os.remove(zip_path)
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

@router.delete("/image/{image_id}", status_code=200)
def delete_image_by_id(image_id: str, db: Session = Depends(get_db)):
    """
    Delete an image by ID.

    Behaviour:
    - Look up the image in the `images` table.
    - Delete any `image_lookup` rows referencing this image.
    - Optionally decrement `image_count` on related `image_classes`.
    - Delete the image row itself.
    - Delete the corresponding object from Google Cloud Storage.
    """
    image: Image | None = (
        db.query(Image)
        .filter(Image.image_id == image_id)
        .first()
    )

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

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

    # Try to delete from GCS; if it fails, we still commit DB change
    try:
        if str(object_name):
            delete_gcs_image(str(object_name))
    except Exception as exc:
        # Log but don't block the DB delete
        logger.exception(f"Failed to delete GCS object {object_name}: {exc}")

    db.commit()

    return {"status": "ok", "deleted_image_id": image_id}

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
        pitchs = [img.pitch for img in cluster if img.pitch is not None]
        hfovs = [img.hfov for img in cluster if img.hfov is not None]
        vfovs = [img.vfov for img in cluster if img.vfov is not None]
        image_types = list(set([img.image_type for img in cluster if img.image_type is not None]))

        avg_alt = sum(alts) / len(alts) if alts else None
        avg_yaw = sum(yaws) / len(yaws) if yaws else None
        avg_pitch = sum(pitchs) / len(pitchs) if pitchs else None
        avg_hfov = sum(hfovs) / len(hfovs) if hfovs else None
        avg_vfov = sum(vfovs) / len(vfovs) if vfovs else None
        image_type = image_types[0] if len(image_types) == 1 else "multiple"

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
            geom=geom,
            image_type=image_type,
            pitch=avg_pitch,
            hfov=avg_hfov,
            vfov=avg_vfov
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


@router.get(
    "/images/cluster/{cluster_id}",
    status_code=200,
    response_model=ClusterOut,
    tags=["image", "cluster"],
    summary="All the images from a given cluster_id",
    description=(
        "retrieves all the images from a given cluster id using th and returns them using the "
    ),
)
def get_cluster_by_id(cluster_id: str, db: Session = Depends(get_db)):
    image_lookup_rows: List[ImageLookup] = (
        db.query(ImageLookup)
        .filter(ImageLookup.class_id == cluster_id)
        .all()
    )

    if not image_lookup_rows:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Use the relationship to get Image objects
    images_out: List[GetImageOut] = []

    for row in image_lookup_rows:
        image = row.image
        if image is None:
            continue

        signed_url = generate_signed_url(str(image.object_name), expires_in_seconds=3600)
        
        images_out.append(
            GetImageOut(
                image_id=image.image_id,
                name=image.name,
                lon=image.lon,
                lat=image.lat,
                alt_m=image.alt_m,
                yaw_deg=image.yaw_deg,
                created=image.created,
                signed_url=signed_url,
                object_name=image.object_name,
                imported_utc=image.imported_utc,
                image_type=image.image_type,
                pitch=image.pitch,
                hfov=image.hfov,
                vfov=image.vfov
            )
        )

    return ClusterOut(
        cluster_id=cluster_id,
        images=images_out
    )

