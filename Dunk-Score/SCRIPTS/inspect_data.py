import pandas as pd 

files = [
"data/raw/csv/game.csv",
"data/raw/csv/game_info.csv",
"data/raw/csv/game_summary.csv",
"data/raw/csv/line_score.csv",
"data/raw/csv/other_stats.csv",
]

for path in files:
    df = pd.read_csv(path)
    print(f"\n===== {path} =====")
    print(df.columns.tolist())
    print(df.head(2))
