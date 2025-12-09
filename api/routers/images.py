import datetime as dt
import logging
import uuid
import zipfile
import os
import shutil
from typing import cast, List, Optional, Annotated
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Form
from sqlalchemy.orm import Session
from api.db.session import get_db
from api.db.models import Image, ImageClass, ImageLookup
from api.utils.file_handler import save_file
from api.utils.exif import extract_exif_geo
from api.utils.image_management import delete_image_instance
from api.utils.security import get_current_user
from pathlib import Path
from api.utils.gcp import handle_gcs_image_upload, generate_signed_url 
from api.utils.image_classification import cluster_images_by_distance
from api.models.images import GetImageOut, CreateImageOut, CreateImagesOut, BaseImage, DeleteImagesRequest, ImageListItem, ImageListResponse, ImageSignedUrlOut, ImageIdsIn
from api.models.clusters import ClusterRequest, ClusterSummary, ClusterOut
from api.models.auth import UserOut

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
    current_user: Annotated[UserOut, Depends(get_current_user)],
    file: UploadFile = File(
        ...,
        description="The drone image file to upload (e.g. JPEG with EXIF GPS data).",
    ),
    category: str = Form(...),
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
    exif_name, exif_lon, exif_lat, exif_alt, exif_yaw, created, geom, image_type, pitch, hfov, vfov, target_range, target_lon, target_lat = extract_exif_geo(file_path)
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
        vfov=vfov,
        target_range=target_range,
        target_lon=target_lon,
        target_lat=target_lat,
        category=category
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
    current_user: Annotated[UserOut, Depends(get_current_user)],
    file: UploadFile = File(
        ...,
        description="A .zip file containing drone image files to upload",
    ),
    category: str = Form(...),
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
                    target_range, 
                    target_lon, 
                    target_lat
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
                    target_range=target_range,
                    target_lon=target_lon,
                    target_lat=target_lat,
                    category=category
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

@router.post("/images/ids", response_model=list[ImageSignedUrlOut])
def get_images_by_ids(
    current_user: Annotated[UserOut, Depends(get_current_user)],
    payload: ImageIdsIn,
    db: Session = Depends(get_db),
):
    # Fetch all images whose IDs are in the provided list
    images = (
        db.query(Image)
        .filter(Image.image_id.in_(payload.image_ids))
        .all()
    )

    if not images:
        # Optional – you can also just return []
        raise HTTPException(status_code=404, detail="No images found for given IDs")

    results: list[ImageSignedUrlOut] = []

    for image in images:
        signed_url = generate_signed_url(
            str(image.object_name),
            expires_in_seconds=3600,
        )
        results.append(
            ImageSignedUrlOut(
                image_id=str(image.image_id),
                signed_url=signed_url,
                name=str(image.name)
            )
        )

    return results

@router.get("/images", response_model=ImageListResponse)
def list_images(
    current_user: Annotated[UserOut, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="1-based page index"),
    page_size: int = Query(
        50,
        ge=1,
        le=200,
        description="Page size (max 200 to protect the DB)",
    ),
    image_type: Optional[str] = Query(
        None, description="Filter by image_type (e.g. 'pano', 'photo')"
    ),
    search: Optional[str] = Query(
        None, description="Case-insensitive name contains filter"
    ),
    class_id: Optional[str] = Query(
        None, description="Filter by related ImageClass class_id"
    ),
    created_from: Optional[dt.datetime] = Query(
        None, description="Filter: created >= this UTC datetime"
    ),
    created_to: Optional[dt.datetime] = Query(
        None, description="Filter: created <= this UTC datetime"
    ),
    image_category: Optional[str] = Query(
        None, description="Filter by category (e.g. 'beverley', 'some place')"
    ),
    db: Session = Depends(get_db),
):
    """
    Paged, filterable list of images.

    Intended for grids / selectors where users can:
    - see image metadata
    - filter / search
    - select multiple rows for batch delete, etc.
    """
    query = db.query(Image)

    # Optional join if filtering by class_id
    if class_id:
        query = (
            query.join(ImageLookup, Image.image_id == ImageLookup.image_id)
            .filter(ImageLookup.class_id == class_id)
        )

    if image_type:
        query = query.filter(Image.image_type == image_type)

    if image_category:
        query = query.filter(Image.category == image_category)

    if search:
        like = f"%{search}%"
        query = query.filter(Image.name.ilike(like))

    if created_from:
        query = query.filter(Image.created >= created_from)
    if created_to:
        query = query.filter(Image.created <= created_to)

    # Total before pagination
    total = query.count()

    # Apply ordering + pagination
    # Primary sort by created desc (nulls last), then FID as tie-breaker
    query = (
        query.order_by(
            Image.created.desc().nullslast(),
            Image.FID.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    images = query.all()

    # Explicit mapping keeps the type checker happy
    items = [ImageListItem.model_validate(img) for img in images]

    return ImageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,  # Pydantic uses from_attributes=True to map
    )

@router.delete("/image/{image_id}", status_code=200)
def delete_image_by_id(
        current_user: Annotated[UserOut, Depends(get_current_user)], 
        image_id: str, 
        db: Session = Depends(get_db)
):
    """
    Delete an image by ID.
    """
    image: Image | None = (
        db.query(Image)
        .filter(Image.image_id == image_id)
        .first()
    )

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    gcs_deleted = delete_image_instance(image, db)

    db.commit()

    return {
        "status": "ok",
        "deleted_image_id": image_id,
        "gcs_deleted": gcs_deleted,
    }


@router.delete("/images/batch", status_code=200)
def delete_images_batch(
        current_user: Annotated[UserOut, Depends(get_current_user)], 
        payload: DeleteImagesRequest, 
        db: Session = Depends(get_db)
):
    """
    Delete multiple images by ID.

    Behaviour:
    - Look up all images in `images` table that match the provided IDs.
    - For each found image:
        - Delete `image_lookup` rows referencing it.
        - Decrement `image_count` on related `image_classes`.
        - Delete the image row.
        - Attempt to delete from GCS (errors logged, do not block DB).
    - Commit once at the end.
    - Return summary of deleted and not-found IDs.
    """
    if not payload.image_ids:
        raise HTTPException(status_code=400, detail="No image_ids provided")

    # Load all images that exist for the given IDs
    images: list[Image] = (
        db.query(Image)
        .filter(Image.image_id.in_(payload.image_ids))
        .all()
    )

    found_ids = {img.image_id for img in images}
    not_found_ids = [iid for iid in payload.image_ids if iid not in found_ids]

    results = []
    for img in images:
        gcs_deleted = delete_image_instance(img, db)
        results.append(
            {
                "image_id": img.image_id,
                "gcs_deleted": gcs_deleted,
            }
        )

    db.commit()

    return {
        "status": "ok",
        "deleted": results,
        "not_found": not_found_ids,
    }



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
    current_user: Annotated[UserOut, Depends(get_current_user)],
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
        target_ranges = [img.target_range for img in cluster if img.target_range is not None]
        target_lats = [img.target_lat for img in cluster if img.target_lat is not None]
        target_lons = [img.target_lon for img in cluster if img.target_lon is not None]

        image_types = list(set([img.image_type for img in cluster if img.image_type is not None]))
        categories = list(set([img.category for img in cluster if img.category is not None]))

        avg_alt = sum(alts) / len(alts) if alts else None
        avg_yaw = sum(yaws) / len(yaws) if yaws else None
        avg_pitch = sum(pitchs) / len(pitchs) if pitchs else None
        avg_hfov = sum(hfovs) / len(hfovs) if hfovs else None
        avg_vfov = sum(vfovs) / len(vfovs) if vfovs else None
        
        avg_target_range = sum(target_ranges) / len(target_ranges) if target_ranges else None
        avg_target_lat = sum(target_lats) / len(target_lats) if target_lats else None
        avg_target_lon = sum(target_lons) / len(target_lons) if target_lons else None


        image_type = image_types[0] if len(image_types) == 1 else "multiple"
        category = categories[0] if len(categories) == 1 else "multiple"

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
            vfov=avg_vfov,
            target_range=avg_target_range,
            target_lat=avg_target_lat,
            target_lon=avg_target_lon,
            category=category
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
                vfov=image.vfov,
                target_range=image.target_range,
                target_lat=image.target_lat,
                target_lon=image.target_lon,
                category=image.category
            )
        )

    return ClusterOut(
        cluster_id=cluster_id,
        images=images_out
    )

