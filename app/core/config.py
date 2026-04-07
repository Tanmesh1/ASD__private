from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Commerce Merchant API"
    app_env: str = "development"
    database_url: str | None = None
    mongo_uri: str
    mongo_db_name: str = "agentic_sales_driver"
    redis_url: str | None = None
    upload_dir: str = "uploads"
    temp_upload_dir: str = "temp_uploads"
    temp_upload_max_age_seconds: int = 3600
    base_url: str = "http://localhost:8000"
    api_v1_prefix: str = "/api/v1"
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    cloudinary_product_folder: str = "products"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
