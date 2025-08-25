from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class GlobalConfig(BaseConfig):
    FRONTEND_URL: str
    model_config = SettingsConfigDict(env_prefix="")

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
