"""Carrega os CSVs de data/processed nas tabelas do esquema único (DADOS/sql/init.sql).

Pode ser rodado várias vezes: os dados vão para tabelas temporárias e depois
entram com upsert, sem apagar jogos vindos da ingestão ao vivo nem previsões.
"""
import pandas as pd
from sqlalchemy import text

from common import PROCESSED_DIR, SCHEMA_SQL, get_engine

ID_DTYPES = {
    "external_id": str,
    "game_external_id": str,
    "team_external_id": str,
    "home_team_external_id": str,
    "away_team_external_id": str,
}

STAT_COLUMNS = [
    "wl", "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct",
    "oreb", "dreb", "reb", "ast", "stl", "blk", "tov", "pf", "pts", "plus_minus",
]

UPSERTS = {
    "teams": """
        INSERT INTO teams (external_id, abbreviation, full_name)
        SELECT external_id, abbreviation, full_name FROM stg_teams
        ON CONFLICT (external_id) DO UPDATE SET
            abbreviation = EXCLUDED.abbreviation,
            full_name = EXCLUDED.full_name
    """,
    "games": """
        INSERT INTO games (external_id, game_date, season, season_type, home_team_external_id,
                           away_team_external_id, home_score, away_score, status, source)
        SELECT external_id, game_date::timestamp, season, season_type, home_team_external_id,
               away_team_external_id, home_score::int, away_score::int, status, 'kaggle'
        FROM stg_games
        ON CONFLICT (external_id) DO UPDATE SET
            game_date = EXCLUDED.game_date,
            season = EXCLUDED.season,
            season_type = EXCLUDED.season_type,
            home_score = EXCLUDED.home_score,
            away_score = EXCLUDED.away_score,
            status = EXCLUDED.status,
            updated_at = NOW()
    """,
    "team_game_stats": f"""
        INSERT INTO team_game_stats (game_external_id, team_external_id, game_date, is_home,
                                     {", ".join(STAT_COLUMNS)})
        SELECT game_external_id, team_external_id, game_date::timestamp, is_home,
               {", ".join(STAT_COLUMNS)}
        FROM stg_team_game_stats
        ON CONFLICT (game_external_id, team_external_id) DO UPDATE SET
            {", ".join(f"{c} = EXCLUDED.{c}" for c in STAT_COLUMNS)}
    """,
}


def main():
    engine = get_engine()

    with engine.begin() as conn:
        legacy = conn.execute(text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'teams' AND column_name = 'id'
        """)).first()
        if legacy:
            raise SystemExit(
                "O banco ainda tem o esquema antigo (teams.id). Recrie o volume com "
                "`docker compose down -v` e suba de novo antes de carregar os dados."
            )
        conn.exec_driver_sql(SCHEMA_SQL.read_text(encoding="utf-8"))

    # Ordem importa por causa das chaves estrangeiras.
    for table in ("teams", "games", "team_game_stats"):
        df = pd.read_csv(PROCESSED_DIR / f"{table}.csv", dtype=ID_DTYPES)
        df.to_sql(f"stg_{table}", engine, if_exists="replace", index=False, chunksize=5000, method="multi")

        with engine.begin() as conn:
            conn.execute(text(UPSERTS[table]))
            conn.execute(text(f"DROP TABLE stg_{table}"))

        print(f"{table}: {len(df)} linhas carregadas")

    with engine.begin() as conn:
        conn.execute(text("ANALYZE teams; ANALYZE games; ANALYZE team_game_stats;"))

    print("Carga concluída com sucesso.")


if __name__ == "__main__":
    main()
