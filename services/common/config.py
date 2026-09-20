from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    # JWT Settings
    JWT_SECRET: str = "super_secret_jwt_key_change_in_production_12345!"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Database URLs
    AUTH_DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db"
    CATALOG_DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/catalog_db"
    INVENTORY_DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/inventory_db"
    CHECKOUT_DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/checkout_db"

    # Service URLs
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    CATALOG_SERVICE_URL: str = "http://localhost:8002"
    INVENTORY_SERVICE_URL: str = "http://localhost:8003"
    CHECKOUT_SERVICE_URL: str = "http://localhost:8004"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
