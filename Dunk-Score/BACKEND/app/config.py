from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    REDIS_URL: str = "redis://redis:6379/0"

    BALLDONTLIE_API_KEY: str | None = None
    SPORTRADAR_API_KEY: str | None = None

    MODEL_PATH: str = "/app/ml/model.joblib"
    MODEL_VERSION: str = "baseline-logreg-v2"

    PROJECTED_TOTAL_BASELINE: float = 224.5
    PROJECTED_TOTAL_REFERENCE_PACE: float = 97.0
    PROJECTED_TOTAL_PACE_FACTOR: float = 0.8

    CONFIDENCE_CENTER: float = 0.5
    CONFIDENCE_SCALE: float = 2.0

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()

DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)