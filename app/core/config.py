from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


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
    verify_token: str | None = None
    access_token: str | None = None
    phone_number_id: str | None = None
    whatsapp_graph_api_version: str = "v18.0"
    whatsapp_auto_reply_text: str = "Hello, thanks for your message!"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_intent_model: str = "gpt-5-mini"
    openai_response_model: str = "gpt-5-mini"
    ai_default_store_id: int = 1
    ai_max_search_results: int = 6
    ai_max_images_per_reply: int = 3
    ai_reply_greeting_prefix: str = "Hi"
    ai_greeting_only_response: str = "How can I help you today? You can ask me about any product, price, or category."
    ai_empty_reply_fallback: str = "How can I help you today?"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
