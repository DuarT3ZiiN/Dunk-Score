"""Features pré-jogo de um confronto.

O mesmo SQL é usado pela API (um jogo) e pelo treino (todos os jogos), então
treino e inferência nunca divergem. Só entram jogos anteriores à data da
partida, para não vazar o resultado.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

FORM_WINDOW = 10
MAX_REST_DAYS = 7

FEATURE_COLUMNS = [
    "points_diff",
    "rebounds_diff",
    "assists_diff",
    "turnovers_diff",
    "form_diff",
    "fg_pct_diff",
    "rest_diff",
]

FACTOR_LABELS = {
    "points_diff": "Pontos por jogo",
    "rebounds_diff": "Rebotes por jogo",
    "assists_diff": "Assistências por jogo",
    "turnovers_diff": "Turnovers por jogo",
    "form_diff": "Aproveitamento recente",
    "fg_pct_diff": "Aproveitamento de arremessos",
    "rest_diff": "Dias de descanso",
}


def feature_sql(game_filter: str) -> str:
    """SQL que devolve uma linha de features por jogo que satisfaz `game_filter`.

    `game_filter` é um trecho SQL fixo do código (nunca entrada do usuário);
    valores variáveis devem ir como parâmetros nomeados.
    """
    return f"""
    WITH target AS (
        SELECT
            g.external_id,
            g.game_date,
            g.season,
            g.season_type,
            g.home_score,
            g.away_score,
            g.home_team_external_id,
            g.away_team_external_id
        FROM games g
        WHERE {game_filter}
    ),

    form AS (
        SELECT
            tg.external_id,
            s.side,
            COUNT(t.game_date) AS games,
            AVG(t.pts) AS avg_points,
            AVG(t.reb) AS avg_rebounds,
            AVG(t.ast) AS avg_assists,
            AVG(t.tov) AS avg_turnovers,
            AVG(t.fg_pct) AS avg_fg_pct,
            AVG(CASE WHEN t.wl = 'W' THEN 1.0 WHEN t.wl = 'L' THEN 0.0 END) AS win_rate,
            MAX(t.game_date) AS last_game_date
        FROM target tg
        CROSS JOIN (VALUES ('home'), ('away')) AS s(side)
        LEFT JOIN LATERAL (
            SELECT t.*
            FROM team_game_stats t
            WHERE t.team_external_id = CASE
                    WHEN s.side = 'home' THEN tg.home_team_external_id
                    ELSE tg.away_team_external_id
                END
              AND t.game_date < tg.game_date
            ORDER BY t.game_date DESC
            LIMIT {FORM_WINDOW}
        ) t ON TRUE
        GROUP BY tg.external_id, s.side
    ),

    wide AS (
        SELECT
            tg.*,
            h.games AS home_games,
            a.games AS away_games,
            COALESCE(h.avg_points, 105.0) AS home_avg_points,
            COALESCE(a.avg_points, 105.0) AS away_avg_points,
            COALESCE(h.avg_rebounds, 43.0) - COALESCE(a.avg_rebounds, 43.0) AS rebounds_diff,
            COALESCE(h.avg_assists, 24.0) - COALESCE(a.avg_assists, 24.0) AS assists_diff,
            COALESCE(h.avg_turnovers, 14.0) - COALESCE(a.avg_turnovers, 14.0) AS turnovers_diff,
            COALESCE(h.win_rate, 0.5) - COALESCE(a.win_rate, 0.5) AS form_diff,
            COALESCE(h.avg_fg_pct, 0.46) - COALESCE(a.avg_fg_pct, 0.46) AS fg_pct_diff,
            LEAST(COALESCE(EXTRACT(EPOCH FROM tg.game_date - h.last_game_date) / 86400, 2), {MAX_REST_DAYS})
              - LEAST(COALESCE(EXTRACT(EPOCH FROM tg.game_date - a.last_game_date) / 86400, 2), {MAX_REST_DAYS})
              AS rest_diff
        FROM target tg
        LEFT JOIN form h ON h.external_id = tg.external_id AND h.side = 'home'
        LEFT JOIN form a ON a.external_id = tg.external_id AND a.side = 'away'
    )

    SELECT
        external_id AS game_id,
        game_date,
        season,
        season_type,
        home_score,
        away_score,
        home_games,
        away_games,
        home_avg_points,
        away_avg_points,
        home_avg_points - away_avg_points AS points_diff,
        rebounds_diff,
        assists_diff,
        turnovers_diff,
        form_diff,
        fg_pct_diff,
        rest_diff::float AS rest_diff
    FROM wide
    """


def build_game_feature_row(db: Session, game_external_id: str) -> dict:
    query = text(feature_sql("g.external_id = :game_external_id"))
    row = db.execute(query, {"game_external_id": game_external_id}).mappings().first()

    if not row:
        raise ValueError(f"Game {game_external_id} not found")

    return dict(row)


def to_model_features(row: dict, columns: list[str] = FEATURE_COLUMNS) -> list[float]:
    return [float(row[col]) for col in columns]
