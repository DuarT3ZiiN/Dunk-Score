from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.config import settings


def nba_today() -> date:
    """Data de hoje no fuso da NBA, para não virar o dia às 21h de Brasília."""
    return datetime.now(ZoneInfo(settings.GAMES_TIMEZONE)).date()
