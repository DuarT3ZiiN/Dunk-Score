from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dates import nba_today
from app.db import get_db
from app.schemas import GameOut, PredictionOut, TeamOut
from app.services.predict import ModelNotTrainedError, predict_game_by_external_id

router = APIRouter(prefix="/games", tags=["games"])

GAME_SELECT = """
SELECT
    g.external_id,
    g.game_date,
    g.season,
    g.season_type,
    g.status,
    g.home_score,
    g.away_score,
    g.home_team_external_id,
    g.away_team_external_id,
    th.full_name AS home_team_name,
    th.abbreviation AS home_team_abbreviation,
    ta.full_name AS away_team_name,
    ta.abbreviation AS away_team_abbreviation,
    p.home_win_prob,
    p.away_win_prob,
    p.projected_total,
    p.confidence_score,
    p.factors,
    p.model_version,
    p.updated_at AS prediction_updated_at
FROM games g
LEFT JOIN teams th ON th.external_id = g.home_team_external_id
LEFT JOIN teams ta ON ta.external_id = g.away_team_external_id
LEFT JOIN predictions p ON p.game_external_id = g.external_id
"""


def to_game_out(row) -> GameOut:
    prediction = None
    if row["home_win_prob"] is not None:
        prediction = PredictionOut(
            home_win_prob=row["home_win_prob"],
            away_win_prob=row["away_win_prob"],
            projected_total=row["projected_total"],
            confidence_score=row["confidence_score"],
            factors=row["factors"],
            model_version=row["model_version"],
            updated_at=row["prediction_updated_at"],
        )

    return GameOut(
        game_id=row["external_id"],
        game_date=row["game_date"],
        season=row["season"],
        season_type=row["season_type"],
        status=row["status"],
        home_team=TeamOut(
            external_id=row["home_team_external_id"],
            name=row["home_team_name"],
            abbreviation=row["home_team_abbreviation"],
        ),
        away_team=TeamOut(
            external_id=row["away_team_external_id"],
            name=row["away_team_name"],
            abbreviation=row["away_team_abbreviation"],
        ),
        home_score=row["home_score"],
        away_score=row["away_score"],
        prediction=prediction,
    )


def fetch_games_on(db: Session, day: date) -> list[GameOut]:
    query = text(GAME_SELECT + """
    WHERE g.game_date >= :start AND g.game_date < :end
    ORDER BY g.game_date ASC, g.external_id ASC
    """)
    rows = db.execute(query, {"start": day, "end": day + timedelta(days=1)}).mappings().all()
    return [to_game_out(row) for row in rows]


@router.get("", response_model=list[GameOut])
def list_games(
    game_date: date | None = Query(default=None, alias="date", description="AAAA-MM-DD; padrão: hoje"),
    db: Session = Depends(get_db),
):
    return fetch_games_on(db, game_date or nba_today())


@router.get("/today", response_model=list[GameOut])
def get_today_games(db: Session = Depends(get_db)):
    return fetch_games_on(db, nba_today())


@router.get("/{game_external_id}", response_model=GameOut)
def get_game(game_external_id: str, db: Session = Depends(get_db)):
    query = text(GAME_SELECT + "WHERE g.external_id = :game_external_id")
    row = db.execute(query, {"game_external_id": game_external_id.strip()}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Game not found")

    return to_game_out(row)


@router.post("/{game_external_id}/predict", response_model=GameOut)
def predict_game(game_external_id: str, db: Session = Depends(get_db)):
    game_external_id = game_external_id.strip()
    try:
        predict_game_by_external_id(db, game_external_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return get_game(game_external_id, db)
