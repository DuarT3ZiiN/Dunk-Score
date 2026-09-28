"""Treina o modelo de vitória do mandante e salva o pacote que a API carrega.

Uso (a partir de BACKEND/):
    python -m ml.train [--csv CAMINHO] [--test-seasons 1]

Validação:
- As últimas temporadas ficam de fora como teste (split temporal, sem embaralhar).
- O modelo é escolhido pela validação cruzada temporal no treino; o teste só é
  olhado uma vez, no fim, para reportar métricas honestas.
- O modelo final é reajustado com todos os dados antes de ser salvo.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.services.features import FEATURE_COLUMNS

ML_DIR = Path(__file__).resolve().parent
PROJECT_DIR = ML_DIR.parents[1]
DEFAULT_CSV = PROJECT_DIR / "data" / "processed" / "training_games.csv"
DEFAULT_MODEL = ML_DIR / "model.joblib"
DEFAULT_METRICS = ML_DIR / "metrics.json"

CANDIDATES = {
    "logistic_regression": Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=3000)),
    ]),
    "random_forest": RandomForestClassifier(
        n_estimators=300, max_depth=8, min_samples_leaf=20, random_state=42, n_jobs=-1,
    ),
    "hist_gradient_boosting": HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.05, max_depth=4, random_state=42,
    ),
}


def temporal_split(df: pd.DataFrame, test_seasons: int):
    seasons = sorted(df["season"].unique())
    if len(seasons) <= test_seasons:
        raise ValueError(f"São necessárias mais de {test_seasons} temporadas; o CSV tem {len(seasons)}.")
    test_from = seasons[-test_seasons]
    return df[df["season"] < test_from], df[df["season"] >= test_from], test_from


def test_metrics(y_true, probs) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, probs >= 0.5)),
        "log_loss": float(log_loss(y_true, probs, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y_true, probs)),
        "roc_auc": float(roc_auc_score(y_true, probs)),
    }


def train(csv_path: Path, model_path: Path, metrics_path: Path, test_seasons: int) -> dict:
    df = pd.read_csv(csv_path, parse_dates=["game_date"]).sort_values("game_date")
    train_df, test_df, test_from = temporal_split(df, test_seasons)

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["home_win"].astype(int)
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["home_win"].astype(int)

    # Folds em ordem cronológica: cada fold valida em jogos posteriores ao treino.
    cv = TimeSeriesSplit(n_splits=5)
    cv_results = {}
    for name, model in CANDIDATES.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="neg_log_loss", n_jobs=-1)
        cv_results[name] = float(-scores.mean())
        print(f"{name}: CV log loss = {cv_results[name]:.4f}")

    best_name = min(cv_results, key=cv_results.get)

    evaluated = clone(CANDIDATES[best_name]).fit(X_train, y_train)
    held_out = test_metrics(y_test, evaluated.predict_proba(X_test)[:, 1])
    held_out["baseline_home_always_wins_accuracy"] = float(y_test.mean())

    final_model = clone(CANDIDATES[best_name]).fit(df[FEATURE_COLUMNS], df["home_win"].astype(int))

    trained_at = datetime.now(timezone.utc)
    version = f"{best_name}-{trained_at:%Y%m%d}"

    metrics = {
        "version": version,
        "trained_at": trained_at.isoformat(),
        "best_model": best_name,
        "features": FEATURE_COLUMNS,
        "rows": int(len(df)),
        "train_seasons": [int(train_df["season"].min()), int(train_df["season"].max())],
        "test_seasons": [int(test_from), int(test_df["season"].max())],
        "cv_log_loss": cv_results,
        "test": held_out,
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": final_model, "version": version, "features": FEATURE_COLUMNS, "metrics": metrics},
        model_path,
    )
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Modelo salvo em {model_path}")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--test-seasons", type=int, default=1)
    args = parser.parse_args()
    np.random.seed(42)
    train(args.csv, args.model, args.metrics, args.test_seasons)


if __name__ == "__main__":
    main()
