from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, Text, TIMESTAMP
from sqlalchemy.sql import func

from app.db import Base

# Espelha DADOS/sql/init.sql, que é a fonte da verdade do esquema.


class Team(Base):
    __tablename__ = "teams"
    external_id = Column(Text, primary_key=True)
    abbreviation = Column(Text)
    city = Column(Text)
    nickname = Column(Text)
    full_name = Column(Text, nullable=False)
    conference = Column(Text)
    division = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Game(Base):
    __tablename__ = "games"
    external_id = Column(Text, primary_key=True)
    game_date = Column(TIMESTAMP, nullable=False)
    season = Column(Integer)
    season_type = Column(Text)
    home_team_external_id = Column(Text, ForeignKey("teams.external_id"), nullable=False)
    away_team_external_id = Column(Text, ForeignKey("teams.external_id"), nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    status = Column(Text)
    source = Column(Text, nullable=False, default="kaggle")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class TeamGameStats(Base):
    __tablename__ = "team_game_stats"
    game_external_id = Column(Text, ForeignKey("games.external_id"), primary_key=True)
    team_external_id = Column(Text, ForeignKey("teams.external_id"), primary_key=True)
    game_date = Column(TIMESTAMP, nullable=False)
    is_home = Column(Boolean, nullable=False)
    wl = Column(Text)
    fg_pct = Column(Float)
    reb = Column(Float)
    ast = Column(Float)
    tov = Column(Float)
    pts = Column(Float)
    plus_minus = Column(Float)


class Prediction(Base):
    __tablename__ = "predictions"
    game_external_id = Column(Text, ForeignKey("games.external_id"), primary_key=True)
    model_version = Column(Text, nullable=False)
    home_win_prob = Column(Float, nullable=False)
    away_win_prob = Column(Float, nullable=False)
    projected_total = Column(Float)
    confidence_score = Column(Float)
    factors = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
