import pandas as pd

from common import RAW_DIR

files = [
RAW_DIR / "game.csv",
RAW_DIR / "game_info.csv",
RAW_DIR / "game_summary.csv",
RAW_DIR / "line_score.csv",
RAW_DIR / "other_stats.csv",
]

for path in files:
    df = pd.read_csv(path)
    print(f"\n===== {path} =====")
    print(df.columns.tolist())
    print(df.head(2))
