import json
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[3]

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "points_diff",
    "rebounds_diff",
    "assists_diff",
    "turnovers_diff",
    "form_diff",
    "fg_pct_diff",
]

def evaluate_model(name, model, X_train, y_train, X_test, y_test):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="neg_log_loss", n_jobs=-1)

    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    return {
        "name": name,
        "cv_neg_log_loss_mean": float(cv_scores.mean()),
        "test_accuracy": float(accuracy_score(y_test, preds)),
        "test_log_loss": float(log_loss(y_test, probs)),
        "test_brier_score": float(brier_score_loss(y_test, probs)),
        "test_roc_auc": float(roc_auc_score(y_test, probs)),
        "model": model,
    }

def train(csv_path: str, model_path: str = "artifacts/model.joblib", metrics_path: str = "artifacts/metrics.json"):
    df = pd.read_csv(csv_path)

    X = df[FEATURE_COLUMNS].copy()
    y = df["home_win"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    models = [
        (
            "logistic_regression",
            Pipeline([
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=3000, solver="liblinear"))
            ])
        ),
        (
            "random_forest",
            RandomForestClassifier(
                n_estimators=300,
                max_depth=8,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
        ),
        (
            "hist_gradient_boosting",
            HistGradientBoostingClassifier(
                max_iter=200,
                learning_rate=0.05,
                max_depth=6,
                random_state=42
            )
        ),
    ]

    results = []
    for name, model in models:
        result = evaluate_model(name, model, X_train, y_train, X_test, y_test)
        results.append(result)

    best = max(results, key=lambda r: r["test_roc_auc"])

    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(best["model"], model_path)

    metrics = {
        "best_model": best["name"],
        "features": FEATURE_COLUMNS,
        "results": [
            {
                "name": r["name"],
                "cv_neg_log_loss_mean": r["cv_neg_log_loss_mean"],
                "test_accuracy": r["test_accuracy"],
                "test_log_loss": r["test_log_loss"],
                "test_brier_score": r["test_brier_score"],
                "test_roc_auc": r["test_roc_auc"],
            }
            for r in results
        ],
        "rows": int(len(df)),
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(json.dumps(metrics, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    train(str(BASE_DIR / "data/processed/historical_games_features.csv"))