# api/utils/gcs.py

import os
from urllib.parse import urlparse
from datetime import timedelta
from google.cloud import storage
from api.config import config
import pathlib
import logging

logger = logging.getLogger(__name__)

def get_storage_client() -> storage.Client:
    """
    Returns a Storage client using the explicit service account file.
    This avoids relying on environment on Windows / local dev.
    """
    if not os.path.exists(config.GCS_SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {config.GCS_SERVICE_ACCOUNT_FILE}")
    return storage.Client.from_service_account_json(config.GCS_SERVICE_ACCOUNT_FILE)


def upload_image_to_gcs(local_path: str, dest_blob_name: str) -> str:
    """
    Uploads a local file to GCS and returns the blob name.
    local_path: full path to the image on disk
    dest_blob_name: path/key inside the bucket (e.g. 'images/foo.jpg')
    """
    client = get_storage_client()
    bucket = client.bucket(config.GCS_IMAGES_BUCKET)
    blob = bucket.blob(dest_blob_name)

    blob.upload_from_filename(local_path)

    if blob:
        return str(blob.name)
    else:
        raise ValueError("Unable to upload image")


def generate_signed_url(dest_blob_name: str, expires_in_seconds: int = 3600) -> str:
    """
    Generates a V4 signed URL that is valid for the given number of seconds.
    This works even if the bucket is completely private.
    """
    client = get_storage_client()
    bucket = client.bucket(config.GCS_IMAGES_BUCKET)
    blob = bucket.blob(dest_blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=expires_in_seconds),
        method="GET",
    )
    return url

def handle_gcs_image_upload(local_path: str) -> str:
    """
    Uploads the image at local_path to GCS under 'images/{filename_only}',
    returns the GCS object_name, and deletes the local file afterwards.
    """
    filename_only = pathlib.Path(local_path).name
    dest_blob_name = f"images/{filename_only}"

    try:
        object_name = upload_image_to_gcs(local_path, dest_blob_name)
    except Exception as e:
        logger.exception(f"Failed uploading {local_path} to GCS: {e}")
        raise

    # Remove the file after successful upload
    try:
        os.remove(local_path)
        logger.info(f"Deleted temp file {local_path}")
    except Exception as e:
        logger.warning(f"Failed to delete temp file {local_path}: {e}")

    return object_name

def _origin_from_url(url: str) -> str:
    """
    Extracts scheme://host[:port] from a full URL, e.g.
    'https://heathgate.ngis.com.au/drone-image-viewer' -> 'https://heathgate.ngis.com.au'
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def ensure_bucket_cors(extra_origins: list[str] | None = None) -> None:
    """
    Ensures the GCS bucket used for images has the expected CORS configuration.
    Only updates the bucket if the current CORS config differs from the desired one.

    This should be safe to call on every application startup.
    """
    client: storage.Client = get_storage_client()
    bucket = client.bucket(config.GCS_IMAGES_BUCKET)

    # Build the list of allowed origins
    origins: list[str] = []

    # Frontend URL from config (prod/dev)
    if config.FRONTEND_URL:
        origins.append(_origin_from_url(config.FRONTEND_URL))

    # Any extra origins (e.g. localhost, additional environments)
    if extra_origins:
        origins.extend(extra_origins)

    # De-duplicate while preserving order
    seen = set()
    unique_origins: list[str] = []
    for o in origins:
        if o and o not in seen:
            seen.add(o)
            unique_origins.append(o)

    if not unique_origins:
        logger.warning("No origins configured for GCS CORS; skipping CORS setup.")
        return

    desired_cors = [
        {
            "origin": unique_origins,
            "method": ["GET", "HEAD", "OPTIONS"],
            "responseHeader": ["Content-Type"],
            "maxAgeSeconds": 3600,
        }
    ]

    current_cors = bucket.cors or []

    if current_cors == desired_cors:
        logger.info(
            "GCS bucket %s already has desired CORS configuration; no update needed.",
            bucket.name,
        )
        return

    logger.info(
        "Updating CORS configuration on GCS bucket %s. Origins: %s",
        bucket.name,
        ", ".join(unique_origins),
    )
    bucket.cors = desired_cors
    bucket.patch()
    logger.info("CORS configuration updated on bucket %s", bucket.name)

def delete_gcs_image(object_name: str) -> None:
    """
    Delete an image object from the configured GCS bucket.
    """
    client = storage.Client()
    bucket = client.bucket(config.GCS_IMAGES_BUCKET)
    blob = bucket.blob(object_name)

    # blob.delete() is idempotent: if not found, it raises NotFound; you can catch/log if you want
    blob.delete()

