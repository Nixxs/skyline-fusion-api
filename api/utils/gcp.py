# api/utils/gcs.py

import os
from datetime import timedelta
from google.cloud import storage
from api.config import config
import pathlib

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

    # Optional: content type
    # blob.content_type = "image/jpeg"
    # blob.patch()

    return blob.name


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
    and returns a signed URL valid for 1 hour.
    """
    filename_only = pathlib.Path(local_path).name
    dest_blob_name = f"images/{filename_only}"
    object_name = upload_image_to_gcs(local_path, dest_blob_name)

    return object_name