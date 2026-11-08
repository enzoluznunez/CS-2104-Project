-- Seeking Pips | Enzo Nunez (enzonunez) | CS 2104, section 83521
-- Honor code: As a Hokie, I will conduct myself with honor and integrity at
--   all times. I will not lie, cheat, or steal, nor will I accept the actions
--   of those who do.
-- LLM use: I used Claude Code by Anthropic for code generation and debugging.

-- Seeking Pips database schema.
-- assets and prices are loaded from data/*.csv; players and bets are
-- created by people using the site.

CREATE TABLE IF NOT EXISTS assets (
    symbol    TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    category  TEXT NOT NULL,
    pip_size  REAL NOT NULL  -- price move that counts as one "pip"
);

CREATE TABLE IF NOT EXISTS prices (
    symbol  TEXT NOT NULL REFERENCES assets(symbol),
    date    TEXT NOT NULL,   -- ISO format, so text ordering is date ordering
    close   REAL NOT NULL,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS players (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id    INTEGER NOT NULL REFERENCES players(id),
    symbol       TEXT NOT NULL REFERENCES assets(symbol),
    direction    TEXT NOT NULL CHECK (direction IN ('buy', 'sell')),
    stake        REAL NOT NULL CHECK (stake > 0),
    entry_date   TEXT NOT NULL,
    exit_date    TEXT NOT NULL,
    entry_price  REAL NOT NULL,
    exit_price   REAL NOT NULL,
    pips         REAL NOT NULL,
    profit       REAL NOT NULL,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Optional stop loss, as the % of the stake the player is willing to lose.
    -- Older databases get these three columns added by db.init_db.
    stop_loss          REAL CHECK (stop_loss IS NULL OR stop_loss > 0),
    stopped_out        INTEGER NOT NULL DEFAULT 0,  -- 1 if the stop closed the bet
    planned_exit_date  TEXT  -- exit the player asked for; exit_date is when it closed
);

CREATE INDEX IF NOT EXISTS idx_bets_player ON bets(player_id);
