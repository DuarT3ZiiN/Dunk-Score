from celery import Celery

from app.config import settings

celery = Celery(
    "nba_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.jobs"],
)

celery.conf.timezone = "America/Sao_Paulo"
celery.conf.beat_schedule = {
    # A sincronização já dispara as previsões ao terminar.
    "sync-games-every-2-hours": {
        "task": "app.tasks.jobs.sync_games_today",
        "schedule": 60.0 * 60.0 * 2,
    },
}
