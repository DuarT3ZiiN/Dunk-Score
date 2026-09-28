"""Gera data/processed/training_games.csv com as mesmas features que a API usa."""
import argparse
import sys

import pandas as pd
from sqlalchemy import text

from common import BACKEND_DIR, PROCESSED_DIR, get_engine

sys.path.insert(0, str(BACKEND_DIR))
from app.services.features import FEATURE_COLUMNS, feature_sql  # noqa: E402

TRAINING_FILTER = """
    g.season_type IN ('Regular Season', 'Playoffs')
    AND g.home_score IS NOT NULL
    AND g.away_score IS NOT NULL
    AND g.season >= :min_season
"""

# Times com pouco histórico geram features pouco confiáveis (começo da base).
MIN_PRIOR_GAMES = 5


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-season", type=int, default=2000,
                        help="Primeira temporada usada (o jogo dos anos 60 não é o de hoje).")
    args = parser.parse_args()

    engine = get_engine()
    df = pd.read_sql(text(feature_sql(TRAINING_FILTER)), engine, params={"min_season": args.min_season})

    df = df[(df["home_games"] >= MIN_PRIOR_GAMES) & (df["away_games"] >= MIN_PRIOR_GAMES)].copy()
    df["home_win"] = (df["home_score"] > df["away_score"]).astype(int)
    df["total_points"] = df["home_score"] + df["away_score"]
    df = df.sort_values("game_date")

    columns = ["game_id", "game_date", "season", "season_type", "home_avg_points", "away_avg_points",
               *FEATURE_COLUMNS, "home_win", "total_points"]
    out = PROCESSED_DIR / "training_games.csv"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df[columns].to_csv(out, index=False)

    print(df[columns].head())
    print(df.shape)
    print(f"Arquivo salvo em {out}")


if __name__ == "__main__":
    main()
