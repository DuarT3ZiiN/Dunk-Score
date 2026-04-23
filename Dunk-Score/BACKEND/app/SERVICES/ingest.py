from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Team, Game
from app.services.providers.balldontlie import get_games_by_date, get_teams

def upsert_team(db: Session, team_payload: dict) -> Team:
    external_id = str(team_payload["id"])
    team = db.query(Team).filter(Team.external_id == external_id).first()
    if not team:
        team = Team(
            external_id=external_id,
            name=team_payload["full_name"],
            abbreviation=team_payload.get("abbreviation"),
            conference=team_payload.get("conference"),
            division=team_payload.get("division"),
        )
        db.add(team)
        db.flush()
    return team

def sync_teams(db: Session):
    payload = get_teams()
    for team_payload in payload.get("data", []):
        upsert_team(db, team_payload)
    db.commit()

def sync_games_for_date(db: Session, date_str: str):
    payload = get_games_by_date(date_str)

    for game_payload in payload.get("data", []):
        home = upsert_team(db, game_payload["home_team"])
        away = upsert_team(db, game_payload["visitor_team"])

        external_id = str(game_payload["id"])
        game = db.query(Game).filter(Game.external_id == external_id).first()
        if not game:
            game = Game(
                external_id=external_id,
                game_date=datetime.fromisoformat(game_payload["date"].replace("Z", "+00:00")),
                home_team_id=home.id,
                away_team_id=away.id,
                home_score=game_payload.get("home_team_score"),
                away_score=game_payload.get("visitor_team_score"),
                status=game_payload.get("status"),
                season=game_payload.get("season"),
            )
            db.add(game)
        else:
            game.home_score = game_payload.get("home_team_score")
            game.away_score = game_payload.get("visitor_team_score")
            game.status = game_payload.get("status")
    db.commit()