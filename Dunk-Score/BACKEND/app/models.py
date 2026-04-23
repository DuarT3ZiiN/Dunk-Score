from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, nullable=False)
    name = Column(Text, nullable=False)
    abbreviation = Column(Text)
    conference = Column(Text)
    division = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, nullable=False)
    game_date = Column(TIMESTAMP, nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    home_score = Column(Integer)
    away_score = Column(Integer)
    status = Column(Text)
    season = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class TeamGameStats(Base):
    __tablename__ = "team_game_stats"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    offensive_rating = Column(Numeric)
    defensive_rating = Column(Numeric)
    net_rating = Column(Numeric)
    pace = Column(Numeric)
    efg_pct = Column(Numeric)
    ts_pct = Column(Numeric)
    tov_pct = Column(Numeric)
    reb_pct = Column(Numeric)
    last5_wins = Column(Integer)
    last10_wins = Column(Integer)
    days_rest = Column(Integer)
    is_back_to_back = Column(Boolean)
    is_home = Column(Boolean)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    model_version = Column(Text, nullable=False)
    home_win_prob = Column(Numeric, nullable=False)
    away_win_prob = Column(Numeric, nullable=False)
    projected_total = Column(Numeric)
    confidence_score = Column(Numeric)
    factors = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())