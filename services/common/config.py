import os

from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super_secret_jwt_key_change_in_production_12345!")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

    # Database URLs
    AUTH_DB_URL: str = os.getenv("AUTH_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db")
    CATALOG_DB_URL: str = os.getenv(
        "CATALOG_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/catalog_db"
    )
    INVENTORY_DB_URL: str = os.getenv(
        "INVENTORY_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/inventory_db"
    )
    CHECKOUT_DB_URL: str = os.getenv(
        "CHECKOUT_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/checkout_db"
    )

    # Service URLs
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    CATALOG_SERVICE_URL: str = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8002")
    INVENTORY_SERVICE_URL: str = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003")
    CHECKOUT_SERVICE_URL: str = os.getenv("CHECKOUT_SERVICE_URL", "http://localhost:8004")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
