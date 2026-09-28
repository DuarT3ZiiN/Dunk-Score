from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TeamOut(BaseModel):
    external_id: str
    name: str | None = None
    abbreviation: str | None = None


class PredictionOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    home_win_prob: float
    away_win_prob: float
    projected_total: float | None = None
    confidence_score: float | None = None
    factors: list[dict[str, Any]] | None = None
    model_version: str | None = None
    updated_at: datetime | None = None


class GameOut(BaseModel):
    game_id: str
    game_date: datetime
    season: int | None = None
    season_type: str | None = None
    status: str | None = None
    home_team: TeamOut
    away_team: TeamOut
    home_score: int | None = None
    away_score: int | None = None
    prediction: PredictionOut | None = None
