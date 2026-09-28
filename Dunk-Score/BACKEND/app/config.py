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

    # Gerado por ml/train.py. O pacote salvo já carrega a versão e as features.
    MODEL_PATH: str = "/app/ml/model.joblib"

    # Fuso usado para decidir qual é o "hoje" da NBA.
    GAMES_TIMEZONE: str = "America/New_York"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

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
