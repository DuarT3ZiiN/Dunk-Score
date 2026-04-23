from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PredictionOut(BaseModel):
    game_id: str
    home_win_prob: float
    away_win_prob: float
    projected_total: float | None = None
    confidence_score: float | None = None
    factors: Any | None = None


class GameOut(BaseModel):
    game_id: str
    status: str | None = None
    game_date: str
    home_team: str
    away_team: str
    prediction: PredictionOut | None = None


class GameCreateIn(BaseModel):
    external_id: str = Field(..., min_length=1, max_length=50)
    game_date: datetime
    home_team_id: int = Field(..., gt=0)
    away_team_id: int = Field(..., gt=0)
    season: int = Field(..., ge=1946)


class TeamCreateIn(BaseModel):
    external_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=120)
    abbreviation: str | None = Field(default=None, max_length=10)
    conference: str | None = Field(default=None, max_length=30)
    division: str | None = Field(default=None, max_length=30)


class PredictionManualIn(BaseModel):
    game_id: int = Field(..., gt=0)
    home_win_prob: float = Field(..., ge=0.0, le=1.0)
    away_win_prob: float = Field(..., ge=0.0, le=1.0)
    projected_total: float | None = None
    confidence_score: float | None = None
    factors: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")