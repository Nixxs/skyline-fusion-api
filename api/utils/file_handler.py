# api/utils/files.py
import os
import time
import logging
import re
from pathlib import Path
from fastapi import HTTPException, UploadFile
from api.config import config

logger = logging.getLogger("api")


def wait_for_file(file_path: str, timeout: int = 10, check_interval: float = 0.5):
    """
    Wait for a file to become accessible (exists and non-zero size) within timeout.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return True
        time.sleep(check_interval)
    raise FileNotFoundError(f"File not accessible: {file_path}")


def safe_filename(filename: str) -> str:
    """
    Simple 'secure' filename function without needing werkzeug.
    - strips path components
    - replaces bad chars with '_'
    """
    name = os.path.basename(filename)
    # Replace anything not alphanumeric, dot, dash, underscore
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


async def save_file(input_file: UploadFile, subfolder: str = "images") -> str:
    """
    Save an uploaded file under config.DATA_PATH / subfolder and return the full path.
    """
    base_dir = Path(config.DATA_PATH)  # you'll add DATA_PATH to your config/env
    job_dir = base_dir / subfolder
    job_dir.mkdir(parents=True, exist_ok=True)

    filename = safe_filename(input_file.filename or "upload.bin")
    file_path = job_dir / filename

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(await input_file.read())

    # Ensure it's actually there and non-empty
    try:
        wait_for_file(str(file_path))
    except FileNotFoundError as e:
        logger.error(f"File save failed or file not accessible: {e}")
        # FastAPI uses 'detail', not 'description'
        raise HTTPException(
            status_code=400,
            detail="File save failed or not accessible."
        )

    logger.info(f"Saved uploaded image to {file_path}")
    return str(file_path)
