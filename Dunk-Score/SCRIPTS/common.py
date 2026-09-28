"""Configuração compartilhada dos scripts de dados."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "BACKEND"
SCHEMA_SQL = PROJECT_DIR / "DADOS" / "sql" / "init.sql"

# Reaproveita as credenciais do docker-compose, se existirem.
load_dotenv(PROJECT_DIR / "DOCKER" / ".env")

DATA_DIR = Path(os.getenv("DUNK_DATA_DIR", PROJECT_DIR / "data"))
RAW_DIR = DATA_DIR / "raw" / "csv"
PROCESSED_DIR = DATA_DIR / "processed"


def database_url() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    # "db" só resolve dentro da rede do docker; os scripts rodam no host.
    if host == "db":
        host = "localhost"
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def get_engine() -> Engine:
    return create_engine(database_url())
