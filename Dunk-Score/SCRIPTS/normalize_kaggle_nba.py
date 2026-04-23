import pandas as pd
from pathlib import Path

RAW = Path("data/raw/csv")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

game = pd.read_csv(RAW / "game.csv")
game_summary = pd.read_csv(RAW / "game_summary.csv")
line_score = pd.read_csv(RAW / "line_score.csv")
other_stats = pd.read_csv(RAW / "other_stats.csv")


# -----------------------------
# 1. TEAMS
# -----------------------------
teams_home = line_score[
    ["team_id_home", "team_abbreviation_home", "team_city_name_home", "team_nickname_home"]
].rename(columns={
    "team_id_home": "external_id",
    "team_abbreviation_home": "abbreviation",
    "team_city_name_home": "city",
    "team_nickname_home": "nickname",
})

teams_away = line_score[
    ["team_id_away", "team_abbreviation_away", "team_city_name_away", "team_nickname_away"]
].rename(columns={
    "team_id_away": "external_id",
    "team_abbreviation_away": "abbreviation",
    "team_city_name_away": "city",
    "team_nickname_away": "nickname",
})

teams = pd.concat([teams_home, teams_away], ignore_index=True).drop_duplicates()
teams["full_name"] = (teams["city"].fillna("") + " " + teams["nickname"].fillna("")).str.strip()
teams = teams.drop_duplicates(subset=["external_id"]).copy()

teams.to_csv(PROCESSED / "teams.csv", index=False)


# -----------------------------
# 2. GAMES
# -----------------------------
games = game[[
    "game_id",
    "game_date",
    "season_id",
    "season_type",
    "team_id_home",
    "team_id_away",
    "pts_home",
    "pts_away",
]].copy()

games = games.rename(columns={
    "game_id": "external_id",
    "game_date": "game_date",
    "season_id": "season_id",
    "season_type": "season_type",
    "team_id_home": "home_team_external_id",
    "team_id_away": "away_team_external_id",
    "pts_home": "home_score",
    "pts_away": "away_score",
})

games["game_date"] = pd.to_datetime(games["game_date"], errors="coerce")

summary_small = game_summary[[
    "game_id",
    "game_status_id",
    "game_status_text",
    "season",
]].copy().rename(columns={"game_id": "external_id"})

games = games.merge(summary_small, on="external_id", how="left")

games["external_id"] = games["external_id"].astype(str).str.strip()
games["home_team_external_id"] = games["home_team_external_id"].astype(str).str.strip()
games["away_team_external_id"] = games["away_team_external_id"].astype(str).str.strip()

games = games.sort_values(["external_id", "game_date"]).drop_duplicates(
    subset=["external_id"],
    keep="first"
)

games.to_csv(PROCESSED / "games.csv", index=False)

# -----------------------------
# 3. TEAM GAME STATS (LONG)
# -----------------------------
base = game.copy()

other = other_stats.copy()

# HOME
home = base[[
    "game_id", "game_date", "season_id", "season_type",
    "team_id_home", "team_abbreviation_home", "team_name_home",
    "wl_home", "fgm_home", "fga_home", "fg_pct_home",
    "fg3m_home", "fg3a_home", "fg3_pct_home",
    "ftm_home", "fta_home", "ft_pct_home",
    "oreb_home", "dreb_home", "reb_home",
    "ast_home", "stl_home", "blk_home", "tov_home", "pf_home",
    "pts_home", "plus_minus_home"
]].copy()

home = home.rename(columns={
    "team_id_home": "team_external_id",
    "team_abbreviation_home": "team_abbreviation",
    "team_name_home": "team_name",
    "wl_home": "wl",
    "fgm_home": "fgm",
    "fga_home": "fga",
    "fg_pct_home": "fg_pct",
    "fg3m_home": "fg3m",
    "fg3a_home": "fg3a",
    "fg3_pct_home": "fg3_pct",
    "ftm_home": "ftm",
    "fta_home": "fta",
    "ft_pct_home": "ft_pct",
    "oreb_home": "oreb",
    "dreb_home": "dreb",
    "reb_home": "reb",
    "ast_home": "ast",
    "stl_home": "stl",
    "blk_home": "blk",
    "tov_home": "tov",
    "pf_home": "pf",
    "pts_home": "pts",
    "plus_minus_home": "plus_minus",
})
home["is_home"] = True

# AWAY
away = base[[
    "game_id", "game_date", "season_id", "season_type",
    "team_id_away", "team_abbreviation_away", "team_name_away",
    "wl_away", "fgm_away", "fga_away", "fg_pct_away",
    "fg3m_away", "fg3a_away", "fg3_pct_away",
    "ftm_away", "fta_away", "ft_pct_away",
    "oreb_away", "dreb_away", "reb_away",
    "ast_away", "stl_away", "blk_away", "tov_away", "pf_away",
    "pts_away", "plus_minus_away"
]].copy()

away = away.rename(columns={
    "team_id_away": "team_external_id",
    "team_abbreviation_away": "team_abbreviation",
    "team_name_away": "team_name",
    "wl_away": "wl",
    "fgm_away": "fgm",
    "fga_away": "fga",
    "fg_pct_away": "fg_pct",
    "fg3m_away": "fg3m",
    "fg3a_away": "fg3a",
    "fg3_pct_away": "fg3_pct",
    "ftm_away": "ftm",
    "fta_away": "fta",
    "ft_pct_away": "ft_pct",
    "oreb_away": "oreb",
    "dreb_away": "dreb",
    "reb_away": "reb",
    "ast_away": "ast",
    "stl_away": "stl",
    "blk_away": "blk",
    "tov_away": "tov",
    "pf_away": "pf",
    "pts_away": "pts",
    "plus_minus_away": "plus_minus",
})
away["is_home"] = False

# merge with other_stats
other_home = other[[
    "game_id", "team_id_home", "pts_paint_home", "pts_2nd_chance_home",
    "pts_fb_home", "largest_lead_home", "lead_changes", "times_tied",
    "team_turnovers_home", "total_turnovers_home", "team_rebounds_home", "pts_off_to_home"
]].rename(columns={
    "team_id_home": "team_external_id",
    "pts_paint_home": "pts_paint",
    "pts_2nd_chance_home": "pts_2nd_chance",
    "pts_fb_home": "pts_fb",
    "largest_lead_home": "largest_lead",
    "team_turnovers_home": "team_turnovers",
    "total_turnovers_home": "total_turnovers",
    "team_rebounds_home": "team_rebounds",
    "pts_off_to_home": "pts_off_to",
})

other_away = other[[
    "game_id", "team_id_away", "pts_paint_away", "pts_2nd_chance_away",
    "pts_fb_away", "largest_lead_away",
    "team_turnovers_away", "total_turnovers_away", "team_rebounds_away", "pts_off_to_away"
]].rename(columns={
    "team_id_away": "team_external_id",
    "pts_paint_away": "pts_paint",
    "pts_2nd_chance_away": "pts_2nd_chance",
    "pts_fb_away": "pts_fb",
    "largest_lead_away": "largest_lead",
    "team_turnovers_away": "team_turnovers",
    "total_turnovers_away": "total_turnovers",
    "team_rebounds_away": "team_rebounds",
    "pts_off_to_away": "pts_off_to",
})

home = home.merge(other_home, on=["game_id", "team_external_id"], how="left")
away = away.merge(other_away, on=["game_id", "team_external_id"], how="left")

team_game_stats = pd.concat([home, away], ignore_index=True)
team_game_stats["game_date"] = pd.to_datetime(team_game_stats["game_date"], errors="coerce")

team_game_stats.to_csv(PROCESSED / "team_game_stats_long.csv", index=False)

print("Arquivos gerados:")
print(PROCESSED / "teams.csv")
print(PROCESSED / "games.csv")
print(PROCESSED / "team_game_stats_long.csv")
