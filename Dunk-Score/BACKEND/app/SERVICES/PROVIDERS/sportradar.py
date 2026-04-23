import requests
from app.config import settings

BASE_URL = "https://api.sportradar.com/nba/trial/v8/en"

def get_daily_schedule(date_str: str) -> dict:
    # date_str: YYYY/MM/DD
    url = f"{BASE_URL}/games/{date_str}/schedule.json"
    resp = requests.get(
        url,
        params={"api_key": settings.SPORTRADAR_API_KEY},
        timeout=20
    )
    resp.raise_for_status()
    return resp.json()

def get_daily_injuries(date_str: str) -> dict:
    url = f"{BASE_URL}/league/{date_str}/injuries.json"
    resp = requests.get(
        url,
        params={"api_key": settings.SPORTRADAR_API_KEY},
        timeout=20
    )
    resp.raise_for_status()
    return resp.json()