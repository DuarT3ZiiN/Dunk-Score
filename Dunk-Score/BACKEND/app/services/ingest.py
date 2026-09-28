"""Ingestão ao vivo (balldontlie) para o mesmo esquema da carga histórica.

Os IDs de time do balldontlie (1-30) não são os IDs oficiais da NBA usados no
Kaggle, então os times são casados pela sigla. Jogos ganham o prefixo "bdl-"
para não colidir com os IDs do Kaggle.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Game, Team, TeamGameStats
from app.services.providers.balldontlie import get_games_by_date, get_teams

GAME_PREFIX = "bdl-"


def resolve_team(db: Session, team_payload: dict) -> str:
    """Devolve o external_id do time, criando-o se ainda não existir."""
    abbreviation = team_payload["abbreviation"]
    existing = db.execute(
        text("""
        SELECT t.external_id
        FROM teams t
        WHERE t.abbreviation = :abbreviation
        ORDER BY (
            SELECT MAX(g.game_date) FROM games g
            WHERE t.external_id IN (g.home_team_external_id, g.away_team_external_id)
        ) DESC NULLS LAST
        LIMIT 1
        """),
        {"abbreviation": abbreviation},
    ).scalar()
    if existing:
        return existing

    external_id = f"{GAME_PREFIX}{team_payload['id']}"
    db.execute(
        insert(Team)
        .values(
            external_id=external_id,
            abbreviation=abbreviation,
            city=team_payload.get("city"),
            nickname=team_payload.get("name"),
            full_name=team_payload["full_name"],
            conference=team_payload.get("conference"),
            division=team_payload.get("division"),
        )
        .on_conflict_do_nothing(index_elements=["external_id"])
    )
    return external_id


def sync_teams(db: Session) -> int:
    payload = get_teams()
    teams = payload.get("data", [])
    for team_payload in teams:
        resolve_team(db, team_payload)
    db.commit()
    return len(teams)


def parse_game_date(game_payload: dict) -> datetime:
    # "date" é a data do jogo no horário dos EUA (AAAA-MM-DD...), a mesma
    # convenção dos dados do Kaggle.
    return datetime.combine(date.fromisoformat(game_payload["date"][:10]), datetime.min.time())


def is_final(game_payload: dict) -> bool:
    return str(game_payload.get("status", "")).lower().startswith("final")


def upsert_final_stats(db: Session, game_id: str, game_date: datetime, team_id: str,
                       is_home: bool, pts: int, opp_pts: int) -> None:
    values = dict(
        game_external_id=game_id,
        team_external_id=team_id,
        game_date=game_date,
        is_home=is_home,
        wl="W" if pts > opp_pts else "L",
        pts=pts,
        plus_minus=pts - opp_pts,
    )
    stmt = insert(TeamGameStats.__table__).values(**values)
    db.execute(stmt.on_conflict_do_update(
        index_elements=["game_external_id", "team_external_id"],
        set_={k: stmt.excluded[k] for k in ("wl", "pts", "plus_minus", "game_date")},
    ))


def sync_games_for_date(db: Session, date_str: str) -> int:
    payload = get_games_by_date(date_str)
    games = payload.get("data", [])

    for game_payload in games:
        home_id = resolve_team(db, game_payload["home_team"])
        away_id = resolve_team(db, game_payload["visitor_team"])
        game_id = f"{GAME_PREFIX}{game_payload['id']}"
        game_date = parse_game_date(game_payload)
        home_score = game_payload.get("home_team_score") or None
        away_score = game_payload.get("visitor_team_score") or None

        stmt = insert(Game).values(
            external_id=game_id,
            game_date=game_date,
            season=game_payload.get("season"),
            season_type="Playoffs" if game_payload.get("postseason") else "Regular Season",
            home_team_external_id=home_id,
            away_team_external_id=away_id,
            home_score=home_score,
            away_score=away_score,
            status=game_payload.get("status"),
            source="balldontlie",
        )
        db.execute(stmt.on_conflict_do_update(
            index_elements=["external_id"],
            set_={
                "game_date": stmt.excluded.game_date,
                "home_score": stmt.excluded.home_score,
                "away_score": stmt.excluded.away_score,
                "status": stmt.excluded.status,
                "updated_at": datetime.utcnow(),
            },
        ))

        # Jogos encerrados viram histórico para as features dos próximos jogos.
        # O plano gratuito só traz o placar, então apenas pontos e V/D são gravados.
        if is_final(game_payload) and home_score is not None and away_score is not None:
            upsert_final_stats(db, game_id, game_date, home_id, True, home_score, away_score)
            upsert_final_stats(db, game_id, game_date, away_id, False, away_score, home_score)

    db.commit()
    return len(games)
