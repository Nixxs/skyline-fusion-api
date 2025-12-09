from functools import lru_cache
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class GlobalConfig(BaseConfig):
    FRONTEND_URL: str
    DATABASE_PATH: str
    DATA_PATH: str
    EXIF_TOOL_PATH: str

    GCS_IMAGES_BUCKET: str
    GCS_SERVICE_ACCOUNT_FILE: str

    ADMIN_USER_EMAIL: str
    ADMIN_USER_PASSWORD_HASH: str

    JWT_SECRET: str

    model_config = SettingsConfigDict(env_prefix="")

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        # Ensure absolute path for SQLite
        path = Path(self.DATABASE_PATH).resolve()
        return f"gpkg:///{path}"

    def __init__(self, **values):
        super().__init__(**values)

class DevConfig(GlobalConfig):
    pass

class TestConfig(GlobalConfig):
    pass

@lru_cache()
def get_config(env_state: str):
    match env_state:
        case "test":
            return TestConfig()
        case "dev":
            return DevConfig()
        case _:
            return GlobalConfig()


config = get_config(BaseConfig().ENV_STATE)
