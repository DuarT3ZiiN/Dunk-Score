CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    abbreviation TEXT,
    conference TEXT,
    division TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) UNIQUE NOT NULL,
    team_id INT REFERENCES teams(id),
    full_name TEXT NOT NULL,
    position TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) UNIQUE NOT NULL,
    game_date TIMESTAMP NOT NULL,
    home_team_id INT REFERENCES teams(id),
    away_team_id INT REFERENCES teams(id),
    home_score INT,
    away_score INT,
    status TEXT,
    season INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS injuries (
    id SERIAL PRIMARY KEY,
    game_external_id VARCHAR(50),
    player_external_id VARCHAR(50),
    team_external_id VARCHAR(50),
    player_name TEXT,
    status TEXT,
    description TEXT,
    report_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS team_game_stats (
    id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(id),
    team_id INT REFERENCES teams(id),
    offensive_rating NUMERIC,
    defensive_rating NUMERIC,
    net_rating NUMERIC,
    pace NUMERIC,
    efg_pct NUMERIC,
    ts_pct NUMERIC,
    tov_pct NUMERIC,
    reb_pct NUMERIC,
    last5_wins INT,
    last10_wins INT,
    days_rest INT,
    is_back_to_back BOOLEAN,
    is_home BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, team_id)
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(id),
    model_version TEXT NOT NULL,
    home_win_prob NUMERIC NOT NULL,
    away_win_prob NUMERIC NOT NULL,
    projected_total NUMERIC,
    confidence_score NUMERIC,
    factors JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_predictions_game ON predictions(game_id);