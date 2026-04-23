from app.services.predict import compute_confidence, compute_projected_total


def test_compute_confidence():
    assert compute_confidence(0.5) == 0.0
    assert compute_confidence(0.8) == 0.6


def test_compute_projected_total():
    row = {
        "home_pace": 100.0,
        "away_pace": 98.0,
    }
    total = compute_projected_total(row)
    assert isinstance(total, float)
    assert total > 0