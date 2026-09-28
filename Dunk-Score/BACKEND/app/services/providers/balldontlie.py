import requests
from app.config import settings

BASE_URL = "https://api.balldontlie.io/v1"

def _headers():
    return {
        "Authorization": settings.BALLDONTLIE_API_KEY
    }

def get_games_by_date(date_str: str) -> dict:
    resp = requests.get(
        f"{BASE_URL}/games",
        headers=_headers(),
        params={"dates[]": date_str},
        timeout=20
    )
    resp.raise_for_status()
    return resp.json()

def get_teams() -> dict:
    resp = requests.get(
        f"{BASE_URL}/teams",
        headers=_headers(),
        timeout=20
    )
    resp.raise_for_status()
    return resp.json()