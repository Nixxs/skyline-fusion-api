import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware

from api.routers.helloworld import router as user_router
from api.routers.images import router as image_router

from api.config import config
from api.logging_conf import configure_logging
from api.db.init_db import init_db

from api.utils.gcp import ensure_bucket_cors

logger = logging.getLogger(__name__)


# CORS settings
origins = [
    config.FRONTEND_URL,  # Add production frontend domain at some point
    "http://localhost:8080"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting API")
    logger.info(f"Database URL: {config.SQLALCHEMY_DATABASE_URL}")
    init_db()
    ensure_bucket_cors(
        extra_origins=[
            "http://localhost:8080",
            "http://localhost:5173",
        ]
    )

    yield
    logger.info("API shutdown complete")

app = FastAPI(
    title="Skyline Fusion API - Heathgate Edition",
    version="1.0.0",
    description="""
This API provides the backend services for the Drone Image Viewer platform used to ingest, catalogue, classify, and visualise aerial imagery captured across the Heathgate region. It supports the upload of drone imagery (JPEG/PNG), automatic extraction of geospatial EXIF metadata, and storage of image records and associated properties within the system database.

Key capabilities include:
• Secure image upload with validation and automated file-system storage.
• Extraction of GPS latitude/longitude, altitude, heading/yaw, and timestamp metadata.
• Persistent indexing of image records for search, filtering, and spatial queries.
• Integration with the Skyline Fusion Viewer for spatial display of drone imagery on map layers.
• Support for custom attributes such as image classification, survey campaign, and operational context.
• RESTful endpoints for listing, retrieving, and managing stored images.

This API underpins the operational workflow for field survey imagery management, enabling rapid QA, spatial review, and streamlined access to critical geospatial photo evidence.
    """,
    contact={
        "name": "Nicholas Chai",
        "email": "nicholasc@ngis.com.au",
    },
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific frontend origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.add_middleware(CorrelationIdMiddleware)

# Include routers
app.include_router(user_router)
app.include_router(image_router)

@app.exception_handler(HTTPException)
async def http_exception_handler_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")
    return await http_exception_handler(request, exc)
