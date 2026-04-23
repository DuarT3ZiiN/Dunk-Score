from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import joblib
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.services.features import build_game_feature_row, to_model_features


_MODEL = None


@dataclass(slots=True)
class PredictionResult:
    home_win_prob: float
    away_win_prob: float
    confidence_score: float
    factors: dict[str, Any]


def load_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = joblib.load(settings.MODEL_PATH)
    return _MODEL


def compute_confidence(home_prob: float) -> float:
    return round(abs(home_prob - 0.5) * 2, 4)


def build_factors(feature_row: dict[str, Any]) -> dict[str, float]:
    return {
        "points_diff": float(feature_row["home_avg_points"]) - float(feature_row["away_avg_points"]),
        "rebounds_diff": float(feature_row["home_avg_rebounds"]) - float(feature_row["away_avg_rebounds"]),
        "assists_diff": float(feature_row["home_avg_assists"]) - float(feature_row["away_avg_assists"]),
        "turnovers_diff": float(feature_row["home_avg_turnovers"]) - float(feature_row["away_avg_turnovers"]),
        "form_diff": float(feature_row["home_last10_wins"]) - float(feature_row["away_last10_wins"]),
        "fg_pct_diff": float(feature_row["home_fg_pct"]) - float(feature_row["away_fg_pct"]),
    }


def infer_game(feature_row: dict[str, Any]) -> PredictionResult:
    model = load_model()
    X = np.array([to_model_features(feature_row)], dtype=float)

    home_prob = float(model.predict_proba(X)[0][1])
    away_prob = 1.0 - home_prob

    return PredictionResult(
        home_win_prob=round(home_prob, 6),
        away_win_prob=round(away_prob, 6),
        confidence_score=compute_confidence(home_prob),
        factors=build_factors(feature_row),
    )


def upsert_prediction(db: Session, game_external_id: str, result: PredictionResult) -> None:
    db.execute(
        text("""
        CREATE TABLE IF NOT EXISTS predictions_kaggle (
            game_external_id TEXT PRIMARY KEY,
            model_version TEXT,
            home_win_prob FLOAT,
            away_win_prob FLOAT,
            confidence_score FLOAT,
            factors JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """)
    )

    db.execute(
        text("""
        INSERT INTO predictions_kaggle (
            game_external_id,
            model_version,
            home_win_prob,
            away_win_prob,
            confidence_score,
            factors,
            updated_at
        )
        VALUES (
            :game_external_id,
            :model_version,
            :home_win_prob,
            :away_win_prob,
            :confidence_score,
            CAST(:factors AS JSONB),
            NOW()
        )
        ON CONFLICT (game_external_id)
        DO UPDATE SET
            model_version = EXCLUDED.model_version,
            home_win_prob = EXCLUDED.home_win_prob,
            away_win_prob = EXCLUDED.away_win_prob,
            confidence_score = EXCLUDED.confidence_score,
            factors = EXCLUDED.factors,
            updated_at = NOW()
        """),
        {
            "game_external_id": game_external_id,
            "model_version": settings.MODEL_VERSION,
            "home_win_prob": result.home_win_prob,
            "away_win_prob": result.away_win_prob,
            "confidence_score": result.confidence_score,
            "factors": __import__("json").dumps(result.factors),
        }
    )
    db.commit()


def predict_game_by_external_id(db: Session, game_external_id: str) -> PredictionResult:
    feature_row = build_game_feature_row(db, game_external_id)
    result = infer_game(feature_row)
    upsert_prediction(db, game_external_id, result)
    return result