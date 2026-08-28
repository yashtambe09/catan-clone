CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    winner_id INTEGER REFERENCES users(id),
    player_count INTEGER NOT NULL CHECK (player_count BETWEEN 2 AND 6),
    board_size TEXT NOT NULL CHECK (board_size IN ('19-hex', '30-hex'))
);

CREATE TABLE game_players (
    game_id INTEGER NOT NULL REFERENCES games(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    final_score INTEGER,
    placement INTEGER,
    PRIMARY KEY (game_id, user_id)
);
