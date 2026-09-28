-- Esquema único do Dunk-Score.
-- Todas as tabelas usam o external_id (texto) como chave, para que a carga
-- histórica (Kaggle) e a ingestão ao vivo (balldontlie) escrevam no mesmo lugar.

CREATE TABLE IF NOT EXISTS teams (
    external_id TEXT PRIMARY KEY,
    abbreviation TEXT,
    city TEXT,
    nickname TEXT,
    full_name TEXT NOT NULL,
    conference TEXT,
    division TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS games (
    external_id TEXT PRIMARY KEY,
    game_date TIMESTAMP NOT NULL,
    season INT,
    season_type TEXT,
    home_team_external_id TEXT NOT NULL REFERENCES teams(external_id),
    away_team_external_id TEXT NOT NULL REFERENCES teams(external_id),
    home_score INT,
    away_score INT,
    status TEXT,
    source TEXT NOT NULL DEFAULT 'kaggle',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Uma linha por (jogo, time). É a base das features de forma recente.
CREATE TABLE IF NOT EXISTS team_game_stats (
    game_external_id TEXT NOT NULL REFERENCES games(external_id) ON DELETE CASCADE,
    team_external_id TEXT NOT NULL REFERENCES teams(external_id),
    game_date TIMESTAMP NOT NULL,
    is_home BOOLEAN NOT NULL,
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
    PRIMARY KEY (game_external_id, team_external_id)
);

CREATE TABLE IF NOT EXISTS predictions (
    game_external_id TEXT PRIMARY KEY REFERENCES games(external_id) ON DELETE CASCADE,
    model_version TEXT NOT NULL,
    home_win_prob FLOAT NOT NULL,
    away_win_prob FLOAT NOT NULL,
    projected_total FLOAT,
    confidence_score FLOAT,
    factors JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS injuries (
    id SERIAL PRIMARY KEY,
    game_external_id TEXT,
    player_external_id TEXT,
    team_external_id TEXT,
    player_name TEXT,
    status TEXT,
    description TEXT,
    report_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_tgs_team_date ON team_game_stats(team_external_id, game_date DESC);
CREATE INDEX IF NOT EXISTS idx_teams_abbreviation ON teams(abbreviation);
