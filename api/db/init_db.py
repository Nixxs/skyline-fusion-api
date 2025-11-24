# api/db/init_db.py
import logging
from sqlalchemy import text
from api.db.session import Base, engine
from api.db.models import Image, ImageClass, ImageLookup
from api.config import config

logger = logging.getLogger(__name__)

def init_db():
    # Enable foreign_keys and WAL for SQLite
    if config.SQLALCHEMY_DATABASE_URL.startswith("gpkg"):
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.execute(text("PRAGMA foreign_keys=ON;"))

    Base.metadata.create_all(bind=engine)
    logger.info("Database schema created/validated.")
