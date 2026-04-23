from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.predict import predict_game_by_external_id

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/today")
def get_today_games(db: Session = Depends(get_db)):
    query = text("""
    SELECT
        g.external_id,
        g.game_date,
        g.season_type,
        g.home_team_external_id,
        g.away_team_external_id,
        g.home_score,
        g.away_score,

        th.full_name AS home_team_name,
        ta.full_name AS away_team_name,

        p.home_win_prob,
        p.away_win_prob,
        p.confidence_score,
        p.factors,
        p.model_version

    FROM games_kaggle g
    LEFT JOIN teams_kaggle th
        ON TRIM(th.external_id) = TRIM(g.home_team_external_id)
    LEFT JOIN teams_kaggle ta
        ON TRIM(ta.external_id) = TRIM(g.away_team_external_id)
    LEFT JOIN predictions_kaggle p
        ON TRIM(p.game_external_id) = TRIM(g.external_id)

    WHERE g.game_date::date = CURRENT_DATE
    ORDER BY g.game_date ASC
    """)

    rows = db.execute(query).mappings().all()
    return [dict(row) for row in rows]


@router.get("/{game_external_id}")
def get_game(game_external_id: str, db: Session = Depends(get_db)):
    query = text("""
    SELECT
        g.external_id,
        g.game_date,
        g.season_type,
        g.home_team_external_id,
        g.away_team_external_id,
        g.home_score,
        g.away_score,

        th.full_name AS home_team_name,
        ta.full_name AS away_team_name,

        p.home_win_prob,
        p.away_win_prob,
        p.confidence_score,
        p.factors,
        p.model_version

    FROM games_kaggle g
    LEFT JOIN teams_kaggle th
        ON TRIM(th.external_id) = TRIM(g.home_team_external_id)
    LEFT JOIN teams_kaggle ta
        ON TRIM(ta.external_id) = TRIM(g.away_team_external_id)
    LEFT JOIN predictions_kaggle p
        ON TRIM(p.game_external_id) = TRIM(g.external_id)

    WHERE TRIM(g.external_id) = :game_external_id
    LIMIT 1
    """)

    row = db.execute(query, {"game_external_id": game_external_id.strip()}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Game not found")

    return dict(row)


@router.post("/{game_external_id}/predict")
def predict_game(game_external_id: str, db: Session = Depends(get_db)):
    try:
        result = predict_game_by_external_id(db, game_external_id.strip())
        return {
            "game_external_id": game_external_id.strip(),
            "home_win_prob": result.home_win_prob,
            "away_win_prob": result.away_win_prob,
            "confidence_score": result.confidence_score,
            "factors": result.factors,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))