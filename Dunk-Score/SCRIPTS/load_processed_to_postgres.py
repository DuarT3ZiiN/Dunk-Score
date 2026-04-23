import os
import pandas as pd
from sqlalchemy import create_engine, text

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

teams = pd.read_csv("data/processed/teams.csv")
games = pd.read_csv("data/processed/games.csv")
team_game_stats = pd.read_csv("data/processed/team_game_stats_long.csv")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # remove colunas duplicadas
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # normaliza nomes
    df.columns = [str(col).strip() for col in df.columns]

    # converte NaN/NaT para None
    df = df.where(pd.notnull(df), None)

    return df


teams = clean_dataframe(teams)
games = clean_dataframe(games)
team_game_stats = clean_dataframe(team_game_stats)

# tipagem básica
teams["external_id"] = teams["external_id"].astype(str)

games["external_id"] = games["external_id"].astype(str).str.strip()
games["home_team_external_id"] = games["home_team_external_id"].astype(str).str.strip()
games["away_team_external_id"] = games["away_team_external_id"].astype(str).str.strip()

games = games.drop_duplicates()
games = games.sort_values(["external_id", "game_date"]).drop_duplicates(
    subset=["external_id"],
    keep="first"
)
games["game_date"] = pd.to_datetime(games["game_date"], errors="coerce")
games = games.where(pd.notnull(games), None)

team_game_stats["game_id"] = team_game_stats["game_id"].astype(str)
team_game_stats["team_external_id"] = team_game_stats["team_external_id"].astype(str)
team_game_stats["game_date"] = pd.to_datetime(team_game_stats["game_date"], errors="coerce")
team_game_stats = team_game_stats.where(pd.notnull(team_game_stats), None)

# seleciona explicitamente as colunas esperadas
teams = teams[
    ["external_id", "abbreviation", "city", "nickname", "full_name"]
].copy()

games = games[
    [
        "external_id",
        "game_date",
        "season_id",
        "season_type",
        "home_team_external_id",
        "away_team_external_id",
        "home_score",
        "away_score",
        "game_status_id",
        "game_status_text",
        "season",
    ]
].copy()

games["external_id"] = games["external_id"].astype(str).str.strip()

# remove linhas totalmente repetidas
games = games.drop_duplicates()

# mantém só uma linha por jogo
games = games.sort_values(["external_id", "game_date"]).drop_duplicates(
    subset=["external_id"],
    keep="first"
)

dup_games = games[games.duplicated(subset=["external_id"], keep=False)].sort_values("external_id")

print("Quantidade de jogos após deduplicação:", len(games))
print("Duplicados restantes em games:", dup_games["external_id"].nunique())

if not dup_games.empty:
    print(dup_games.head(20))
    raise ValueError("Ainda existem external_id duplicados em games.")

team_game_stats = team_game_stats[
    [
        "game_id",
        "game_date",
        "season_id",
        "season_type",
        "team_external_id",
        "team_abbreviation",
        "team_name",
        "wl",
        "fgm",
        "fga",
        "fg_pct",
        "fg3m",
        "fg3a",
        "fg3_pct",
        "ftm",
        "fta",
        "ft_pct",
        "oreb",
        "dreb",
        "reb",
        "ast",
        "stl",
        "blk",
        "tov",
        "pf",
        "pts",
        "plus_minus",
        "is_home",
        "pts_paint",
        "pts_2nd_chance",
        "pts_fb",
        "largest_lead",
        "lead_changes",
        "times_tied",
        "team_turnovers",
        "total_turnovers",
        "team_rebounds",
        "pts_off_to",
    ]
].copy()

print("Colunas teams:", teams.columns.tolist())
print("Colunas games:", games.columns.tolist())
print("Colunas team_game_stats:", team_game_stats.columns.tolist())

with engine.begin() as conn:
    conn.execute(text("""
        DROP TABLE IF EXISTS teams_kaggle;
        DROP TABLE IF EXISTS games_kaggle;
        DROP TABLE IF EXISTS team_game_stats_long;
    """))

    conn.execute(text("""
        CREATE TABLE teams_kaggle (
            external_id TEXT PRIMARY KEY,
            abbreviation TEXT,
            city TEXT,
            nickname TEXT,
            full_name TEXT
        )
    """))

    conn.execute(text("""
        CREATE TABLE games_kaggle (
            external_id TEXT PRIMARY KEY,
            game_date TIMESTAMP,
            season_id BIGINT,
            season_type TEXT,
            home_team_external_id TEXT,
            away_team_external_id TEXT,
            home_score FLOAT,
            away_score FLOAT,
            game_status_id FLOAT,
            game_status_text TEXT,
            season FLOAT
        )
    """))

    conn.execute(text("""
        CREATE TABLE team_game_stats_long (
            game_id TEXT,
            game_date TIMESTAMP,
            season_id BIGINT,
            season_type TEXT,
            team_external_id TEXT,
            team_abbreviation TEXT,
            team_name TEXT,
            wl TEXT,
            fgm FLOAT,
            fga FLOAT,
            fg_pct FLOAT,
            fg3m FLOAT,
            fg3a FLOAT,
            fg3_pct FLOAT,
            ftm FLOAT,
            fta FLOAT,
            ft_pct FLOAT,
            oreb FLOAT,
            dreb FLOAT,
            reb FLOAT,
            ast FLOAT,
            stl FLOAT,
            blk FLOAT,
            tov FLOAT,
            pf FLOAT,
            pts FLOAT,
            plus_minus FLOAT,
            is_home BOOLEAN,
            pts_paint FLOAT,
            pts_2nd_chance FLOAT,
            pts_fb FLOAT,
            largest_lead FLOAT,
            lead_changes FLOAT,
            times_tied FLOAT,
            team_turnovers FLOAT,
            total_turnovers FLOAT,
            team_rebounds FLOAT,
            pts_off_to FLOAT
        )
    """))

# inserção em chunks
teams.to_sql(
    "teams_kaggle",
    engine,
    if_exists="append",
    index=False,
    chunksize=500,
    method="multi",
)

games.to_sql(
    "games_kaggle",
    engine,
    if_exists="append",
    index=False,
    chunksize=500,
    method="multi",
)

team_game_stats.to_sql(
    "team_game_stats_long",
    engine,
    if_exists="append",
    index=False,
    chunksize=500,
    method="multi",
)

print("Carga concluída com sucesso.")
print(f"teams_kaggle: {len(teams)} linhas")
print(f"games_kaggle: {len(games)} linhas")
print(f"team_game_stats_long: {len(team_game_stats)} linhas")