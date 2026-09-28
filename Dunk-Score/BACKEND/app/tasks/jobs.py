import logging
from datetime import timedelta

from app.dates import nba_today
from app.db import SessionLocal
from app.routes.games import fetch_games_on
from app.services.ingest import sync_games_for_date
from app.services.predict import ModelNotTrainedError, predict_game_by_external_id
from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.jobs.sync_games_today")
def sync_games_today():
    """Busca os jogos de ontem (placares finais) e de hoje, depois recalcula as previsões."""
    today = nba_today()
    db = SessionLocal()
    try:
        synced = {
            str(day): sync_games_for_date(db, str(day))
            for day in (today - timedelta(days=1), today)
        }
    finally:
        db.close()

    predict_today_games.delay()
    return synced


@celery.task(name="app.tasks.jobs.predict_today_games")
def predict_today_games():
    db = SessionLocal()
    try:
        results = []
        for game in fetch_games_on(db, nba_today()):
            try:
                prediction = predict_game_by_external_id(db, game.game_id)
            except ModelNotTrainedError:
                logger.warning("Modelo não treinado; previsões puladas.")
                break
            results.append({
                "game_external_id": game.game_id,
                "home_win_prob": prediction.home_win_prob,
                "away_win_prob": prediction.away_win_prob,
                "projected_total": prediction.projected_total,
            })
        return results
    finally:
        db.close()
