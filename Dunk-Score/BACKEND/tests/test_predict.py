import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from app.services import predict
from app.services.features import FEATURE_COLUMNS, to_model_features
from app.services.predict import (
    build_factors,
    compute_confidence,
    compute_projected_total,
    infer_game,
)
from ml.train import temporal_split


def feature_row(**overrides):
    row = {name: 0.0 for name in FEATURE_COLUMNS}
    row.update(home_avg_points=112.0, away_avg_points=108.5)
    row.update(overrides)
    return row


def test_compute_confidence():
    assert compute_confidence(0.5) == 0.0
    assert compute_confidence(0.8) == 0.6
    assert compute_confidence(0.2) == 0.6


def test_compute_projected_total():
    assert compute_projected_total(feature_row()) == 220.5


def test_to_model_features_follows_column_order():
    row = feature_row(points_diff=3.5, rest_diff=-1.0)
    values = to_model_features(row)
    assert values[FEATURE_COLUMNS.index("points_diff")] == 3.5
    assert values[FEATURE_COLUMNS.index("rest_diff")] == -1.0


def test_build_factors_labels_every_feature():
    factors = build_factors(feature_row(form_diff=0.3), FEATURE_COLUMNS)
    assert [f["feature"] for f in factors] == FEATURE_COLUMNS
    assert next(f for f in factors if f["feature"] == "form_diff")["value"] == 0.3
    assert all(f["label"] for f in factors)


def test_infer_game_uses_bundle(monkeypatch):
    X = pd.DataFrame({"points_diff": [-5.0, 5.0] * 10})
    y = [0, 1] * 10
    model = LogisticRegression().fit(X, y)
    bundle = {"model": model, "version": "test-v1", "features": ["points_diff"]}
    monkeypatch.setattr(predict, "_BUNDLE", bundle)

    result = infer_game(feature_row(points_diff=5.0))

    assert result.model_version == "test-v1"
    assert result.home_win_prob > 0.5
    assert result.home_win_prob + result.away_win_prob == pytest.approx(1.0)
    assert result.projected_total == 220.5


def test_temporal_split_holds_out_latest_seasons():
    df = pd.DataFrame({"season": [2019, 2019, 2020, 2021, 2021]})
    train, test, test_from = temporal_split(df, test_seasons=1)
    assert test_from == 2021
    assert train["season"].max() < test["season"].min()


def test_temporal_split_needs_enough_seasons():
    with pytest.raises(ValueError):
        temporal_split(pd.DataFrame({"season": [2020, 2020]}), test_seasons=1)
