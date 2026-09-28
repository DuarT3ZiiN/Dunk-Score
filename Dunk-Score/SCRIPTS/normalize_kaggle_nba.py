"""Converte o dataset NBA do Kaggle (wyattowalsh/basketball) para os CSVs do esquema único.

Entrada:  data/raw/csv/game.csv
Saída:    data/processed/{teams,games,team_game_stats}.csv
"""
import pandas as pd

from common import PROCESSED_DIR, RAW_DIR

STAT_COLUMNS = [
    "wl", "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct",
    "oreb", "dreb", "reb", "ast", "stl", "blk", "tov", "pf", "pts", "plus_minus",
]


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # IDs como texto para preservar zeros à esquerda (ex.: "0021900001").
    game = pd.read_csv(
        RAW_DIR / "game.csv",
        dtype={"game_id": str, "season_id": str, "team_id_home": str, "team_id_away": str},
    )
    game["game_date"] = pd.to_datetime(game["game_date"], errors="coerce")
    game = (
        game.dropna(subset=["game_date", "team_id_home", "team_id_away"])
        .drop_duplicates(subset=["game_id"])
        .sort_values("game_date")
    )

    # -----------------------------
    # 1. TEAMS: nome e sigla mais recentes de cada franquia
    # -----------------------------
    sides = []
    for side in ("home", "away"):
        sides.append(game[["game_date", f"team_id_{side}", f"team_abbreviation_{side}", f"team_name_{side}"]]
                     .set_axis(["game_date", "external_id", "abbreviation", "full_name"], axis=1))
    teams = (
        pd.concat(sides)
        .sort_values("game_date")
        .drop_duplicates(subset=["external_id"], keep="last")
        .drop(columns="game_date")
    )
    teams.to_csv(PROCESSED_DIR / "teams.csv", index=False)

    # -----------------------------
    # 2. GAMES
    # -----------------------------
    games = pd.DataFrame({
        "external_id": game["game_id"],
        "game_date": game["game_date"],
        # season_id vem como "22019": tipo (1 dígito) + ano de início da temporada.
        "season": game["season_id"].str[-4:].astype(int),
        "season_type": game["season_type"],
        "home_team_external_id": game["team_id_home"],
        "away_team_external_id": game["team_id_away"],
        "home_score": game["pts_home"],
        "away_score": game["pts_away"],
    })
    games["status"] = games["home_score"].notna().map({True: "Final", False: None})
    games.to_csv(PROCESSED_DIR / "games.csv", index=False)

    # -----------------------------
    # 3. TEAM GAME STATS (uma linha por time por jogo)
    # -----------------------------
    frames = []
    for side in ("home", "away"):
        frame = game[["game_id", "game_date", f"team_id_{side}"] + [f"{c}_{side}" for c in STAT_COLUMNS]]
        frame = frame.set_axis(["game_external_id", "game_date", "team_external_id"] + STAT_COLUMNS, axis=1)
        frame["is_home"] = side == "home"
        frames.append(frame)
    team_game_stats = pd.concat(frames, ignore_index=True)
    team_game_stats.to_csv(PROCESSED_DIR / "team_game_stats.csv", index=False)

    print("Arquivos gerados em", PROCESSED_DIR)
    print(f"teams: {len(teams)} | games: {len(games)} | team_game_stats: {len(team_game_stats)}")


if __name__ == "__main__":
    main()
