from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import joblib
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.services.features import FACTOR_LABELS, build_game_feature_row, to_model_features

_BUNDLE: dict[str, Any] | None = None


@dataclass(slots=True)
class PredictionResult:
    home_win_prob: float
    away_win_prob: float
    projected_total: float
    confidence_score: float
    factors: list[dict[str, Any]]
    model_version: str


def load_model_bundle() -> dict[str, Any]:
    """Carrega o pacote salvo por ml/train.py: {model, version, features, ...}."""
    global _BUNDLE
    if _BUNDLE is None:
        try:
            _BUNDLE = joblib.load(settings.MODEL_PATH)
        except FileNotFoundError as exc:
            raise ModelNotTrainedError(
                f"Modelo não encontrado em {settings.MODEL_PATH}. Rode ml/train.py primeiro."
            ) from exc
    return _BUNDLE


class ModelNotTrainedError(RuntimeError):
    pass


def compute_confidence(home_prob: float) -> float:
    return round(abs(home_prob - 0.5) * 2, 4)


def compute_projected_total(feature_row: dict[str, Any]) -> float:
    """Soma das médias de pontos recentes de cada time."""
    return round(float(feature_row["home_avg_points"]) + float(feature_row["away_avg_points"]), 1)


def build_factors(feature_row: dict[str, Any], features: list[str]) -> list[dict[str, Any]]:
    """Diferenças mandante - visitante que alimentam o modelo (positivo favorece o mandante,
    exceto turnovers, onde positivo é pior para o mandante)."""
    return [
        {
            "feature": name,
            "label": FACTOR_LABELS.get(name, name),
            "value": round(float(feature_row[name]), 4),
        }
        for name in features
    ]


def infer_game(feature_row: dict[str, Any]) -> PredictionResult:
    bundle = load_model_bundle()
    features = bundle["features"]
    X = pd.DataFrame([to_model_features(feature_row, features)], columns=features, dtype=float)

    home_prob = float(bundle["model"].predict_proba(X)[0][1])

    return PredictionResult(
        home_win_prob=round(home_prob, 6),
        away_win_prob=round(1.0 - home_prob, 6),
        projected_total=compute_projected_total(feature_row),
        confidence_score=compute_confidence(home_prob),
        factors=build_factors(feature_row, features),
        model_version=bundle["version"],
    )


def upsert_prediction(db: Session, game_external_id: str, result: PredictionResult) -> None:
    db.execute(
        text("""
        INSERT INTO predictions (
            game_external_id, model_version, home_win_prob, away_win_prob,
            projected_total, confidence_score, factors, updated_at
        )
        VALUES (
            :game_external_id, :model_version, :home_win_prob, :away_win_prob,
            :projected_total, :confidence_score, CAST(:factors AS JSONB), NOW()
        )
        ON CONFLICT (game_external_id) DO UPDATE SET
            model_version = EXCLUDED.model_version,
            home_win_prob = EXCLUDED.home_win_prob,
            away_win_prob = EXCLUDED.away_win_prob,
            projected_total = EXCLUDED.projected_total,
            confidence_score = EXCLUDED.confidence_score,
            factors = EXCLUDED.factors,
            updated_at = NOW()
        """),
        {
            "game_external_id": game_external_id,
            "model_version": result.model_version,
            "home_win_prob": result.home_win_prob,
            "away_win_prob": result.away_win_prob,
            "projected_total": result.projected_total,
            "confidence_score": result.confidence_score,
            "factors": json.dumps(result.factors),
        },
    )
    db.commit()


def predict_game_by_external_id(db: Session, game_external_id: str) -> PredictionResult:
    feature_row = build_game_feature_row(db, game_external_id)
    result = infer_game(feature_row)
    upsert_prediction(db, game_external_id, result)
    return result
