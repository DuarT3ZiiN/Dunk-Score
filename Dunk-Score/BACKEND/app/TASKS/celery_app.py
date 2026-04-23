from celery import Celery
from app.config import settings

celery = Celery(
    "nba_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.timezone = "America/Sao_Paulo"
celery.conf.beat_schedule = {
    "sync-games-every-morning": {
        "task": "app.tasks.jobs.sync_games_today",
        "schedule": 60.0 * 60.0 * 6,  # ajuste conforme quiser
    },
    "predict-games-every-2-hours": {
        "task": "app.tasks.jobs.predict_today_games",
        "schedule": 60.0 * 60.0 * 2,
    },
}