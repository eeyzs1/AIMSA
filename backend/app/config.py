from pathlib import Path

from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "aimsa"
    POSTGRES_PASSWORD: str = "aimsa_secret"
    POSTGRES_DB: str = "aimsa"

    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_USER: str = "aimsa"
    MONGO_PASSWORD: str = "aimsa_secret"
    MONGO_DB: str = "aimsa_logs"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    LLM_SERVICE_URL: str = "http://localhost:8001"
    CHROMA_PERSIST_DIR: str = "/data/chroma"
    CHROMA_MODE: str = "persistent"

    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100

    CORS_ORIGINS: str = "*"
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def postgres_sync_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def mongo_url(self) -> str:
        return f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = str(_PROJECT_ROOT / ".env")
        extra = "ignore"


settings = Settings()
