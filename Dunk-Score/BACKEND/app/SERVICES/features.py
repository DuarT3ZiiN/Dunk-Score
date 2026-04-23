from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def build_game_feature_row(db: Session, game_external_id: str) -> dict:
    query = text("""
    WITH target_game AS (
        SELECT
            TRIM(g.external_id) AS external_id,
            g.game_date::timestamp AS game_date,
            TRIM(g.home_team_external_id) AS home_team_external_id,
            TRIM(g.away_team_external_id) AS away_team_external_id
        FROM games_kaggle g
        WHERE TRIM(g.external_id) = :game_external_id
    ),

    home_stats AS (
        SELECT
            tg.external_id,
            AVG(t.pts) AS home_avg_points,
            AVG(t.reb) AS home_avg_rebounds,
            AVG(t.ast) AS home_avg_assists,
            AVG(t.tov) AS home_avg_turnovers,
            AVG(t.fg_pct) AS home_fg_pct,
            SUM(CASE WHEN t.wl = 'W' THEN 1 ELSE 0 END) AS home_last10_wins,
            MAX(t.game_date) AS home_last_game_date
        FROM target_game tg
        LEFT JOIN LATERAL (
            SELECT *
            FROM team_game_stats_long t
            WHERE TRIM(t.team_external_id) = tg.home_team_external_id
              AND t.game_date::timestamp < tg.game_date
            ORDER BY t.game_date DESC
            LIMIT 10
        ) t ON TRUE
        GROUP BY tg.external_id
    ),

    away_stats AS (
        SELECT
            tg.external_id,
            AVG(t.pts) AS away_avg_points,
            AVG(t.reb) AS away_avg_rebounds,
            AVG(t.ast) AS away_avg_assists,
            AVG(t.tov) AS away_avg_turnovers,
            AVG(t.fg_pct) AS away_fg_pct,
            SUM(CASE WHEN t.wl = 'W' THEN 1 ELSE 0 END) AS away_last10_wins,
            MAX(t.game_date) AS away_last_game_date
        FROM target_game tg
        LEFT JOIN LATERAL (
            SELECT *
            FROM team_game_stats_long t
            WHERE TRIM(t.team_external_id) = tg.away_team_external_id
              AND t.game_date::timestamp < tg.game_date
            ORDER BY t.game_date DESC
            LIMIT 10
        ) t ON TRUE
        GROUP BY tg.external_id
    )

    SELECT
        tg.external_id AS game_id,

        COALESCE(h.home_avg_points, 100.0) AS home_avg_points,
        COALESCE(a.away_avg_points, 100.0) AS away_avg_points,

        COALESCE(h.home_avg_rebounds, 40.0) AS home_avg_rebounds,
        COALESCE(a.away_avg_rebounds, 40.0) AS away_avg_rebounds,

        COALESCE(h.home_avg_assists, 20.0) AS home_avg_assists,
        COALESCE(a.away_avg_assists, 20.0) AS away_avg_assists,

        COALESCE(h.home_avg_turnovers, 15.0) AS home_avg_turnovers,
        COALESCE(a.away_avg_turnovers, 15.0) AS away_avg_turnovers,

        COALESCE(h.home_fg_pct, 0.45) AS home_fg_pct,
        COALESCE(a.away_fg_pct, 0.45) AS away_fg_pct,

        COALESCE(h.home_last10_wins, 5.0) AS home_last10_wins,
        COALESCE(a.away_last10_wins, 5.0) AS away_last10_wins,

        COALESCE(EXTRACT(DAY FROM (tg.game_date - h.home_last_game_date)), 2)::float AS home_days_rest,
        COALESCE(EXTRACT(DAY FROM (tg.game_date - a.away_last_game_date)), 2)::float AS away_days_rest

    FROM target_game tg
    LEFT JOIN home_stats h ON h.external_id = tg.external_id
    LEFT JOIN away_stats a ON a.external_id = tg.external_id
    """)
    row = db.execute(query, {"game_external_id": str(game_external_id).strip()}).mappings().first()

    if not row:
        raise ValueError(f"Game {game_external_id} not found")

    return dict(row)


def to_model_features(row: dict) -> list[float]:
    return [
        float(row["home_avg_points"]) - float(row["away_avg_points"]),
        float(row["home_avg_rebounds"]) - float(row["away_avg_rebounds"]),
        float(row["home_avg_assists"]) - float(row["away_avg_assists"]),
        float(row["home_avg_turnovers"]) - float(row["away_avg_turnovers"]),
        float(row["home_last10_wins"]) - float(row["away_last10_wins"]),
        float(row["home_fg_pct"]) - float(row["away_fg_pct"]),
    ]