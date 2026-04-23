from sqlalchemy import text

from app.db import SessionLocal
from app.services.predict import predict_game_by_external_id


def predict_today_games():
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT external_id
            FROM games_kaggle
            WHERE game_date::date = CURRENT_DATE
            ORDER BY game_date ASC
        """)).fetchall()

        results = []
        for row in rows:
            game_external_id = str(row[0]).strip()
            prediction = predict_game_by_external_id(db, game_external_id)
            results.append({
                "game_external_id": game_external_id,
                "home_win_prob": prediction.home_win_prob,
                "away_win_prob": prediction.away_win_prob,
                "confidence_score": prediction.confidence_score,
            })

        return results
    finally:
        db.close()