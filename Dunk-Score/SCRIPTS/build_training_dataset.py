import os
import pandas as pd
from sqlalchemy import create_engine

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres123")
POSTGRES_DB = os.getenv("POSTGRES_DB", "nba")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL)

query = """
WITH base_games AS (
    SELECT
        TRIM(g.external_id) AS external_id,
        g.game_date::timestamp AS game_date,
        TRIM(g.home_team_external_id) AS home_team_external_id,
        TRIM(g.away_team_external_id) AS away_team_external_id,
        CASE
            WHEN g.home_score > g.away_score THEN 1
            ELSE 0
        END AS home_win
    FROM games_kaggle g
    WHERE g.home_score IS NOT NULL
      AND g.away_score IS NOT NULL
),

home_stats AS (
    SELECT
        bg.external_id,
        AVG(t.pts) AS home_avg_points,
        AVG(t.reb) AS home_avg_rebounds,
        AVG(t.ast) AS home_avg_assists,
        AVG(t.tov) AS home_avg_turnovers,
        AVG(t.fg_pct) AS home_fg_pct,
        SUM(CASE WHEN t.wl = 'W' THEN 1 ELSE 0 END) AS home_last10_wins
    FROM base_games bg
    LEFT JOIN LATERAL (
        SELECT *
        FROM team_game_stats_long t
        WHERE TRIM(t.team_external_id) = bg.home_team_external_id
          AND t.game_date::timestamp < bg.game_date
        ORDER BY t.game_date DESC
        LIMIT 10
    ) t ON TRUE
    GROUP BY bg.external_id
),

away_stats AS (
    SELECT
        bg.external_id,
        AVG(t.pts) AS away_avg_points,
        AVG(t.reb) AS away_avg_rebounds,
        AVG(t.ast) AS away_avg_assists,
        AVG(t.tov) AS away_avg_turnovers,
        AVG(t.fg_pct) AS away_fg_pct,
        SUM(CASE WHEN t.wl = 'W' THEN 1 ELSE 0 END) AS away_last10_wins
    FROM base_games bg
    LEFT JOIN LATERAL (
        SELECT *
        FROM team_game_stats_long t
        WHERE TRIM(t.team_external_id) = bg.away_team_external_id
          AND t.game_date::timestamp < bg.game_date
        ORDER BY t.game_date DESC
        LIMIT 10
    ) t ON TRUE
    GROUP BY bg.external_id
)

SELECT
    bg.external_id,
    COALESCE(h.home_avg_points, 100.0) - COALESCE(a.away_avg_points, 100.0) AS points_diff,
    COALESCE(h.home_avg_rebounds, 40.0) - COALESCE(a.away_avg_rebounds, 40.0) AS rebounds_diff,
    COALESCE(h.home_avg_assists, 20.0) - COALESCE(a.away_avg_assists, 20.0) AS assists_diff,
    COALESCE(h.home_avg_turnovers, 15.0) - COALESCE(a.away_avg_turnovers, 15.0) AS turnovers_diff,
    COALESCE(h.home_last10_wins, 5.0) - COALESCE(a.away_last10_wins, 5.0) AS form_diff,
    COALESCE(h.home_fg_pct, 0.45) - COALESCE(a.away_fg_pct, 0.45) AS fg_pct_diff,
    bg.home_win
FROM base_games bg
LEFT JOIN home_stats h ON h.external_id = bg.external_id
LEFT JOIN away_stats a ON a.external_id = bg.external_id
"""
if __name__ == "__main__":
    df = pd.read_sql(query, engine)
    df.to_csv("data/processed/historical_games_features.csv", index=False)

    print(df.head())
    print(df.shape)
    print("Arquivo salvo em data/processed/historical_games_features.csv")