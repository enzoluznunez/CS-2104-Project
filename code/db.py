"""SQLite helpers: one connection per request, plus first-run data loading."""
import csv
import sqlite3
from pathlib import Path

from flask import current_app, g

CODE_DIR = Path(__file__).resolve().parent


def get_db():
    """Return this request's connection, opening it on first use."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # rows behave like dicts in templates
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(database, data_dir):
    """Create the tables and load market data if it is not loaded yet.

    Prices only need loading once, so a database that already has assets is
    left alone. This keeps players and bets when the container restarts.
    """
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database)
    try:
        conn.executescript((CODE_DIR / "schema.sql").read_text())
        _add_missing_columns(conn)
        if conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0:
            _load_csv(conn, Path(data_dir))
        conn.commit()
    finally:
        conn.close()


# Columns added to bets after Week 9. CREATE TABLE IF NOT EXISTS leaves an
# existing table alone, so a database kept in the Docker volume needs them
# added here. Existing bets simply have no stop loss.
NEW_BET_COLUMNS = {
    "stop_loss": "REAL",
    "stopped_out": "INTEGER NOT NULL DEFAULT 0",
    "planned_exit_date": "TEXT",
}


def _add_missing_columns(conn):
    existing = {row[1] for row in conn.execute("PRAGMA table_info(bets)")}
    for name, definition in NEW_BET_COLUMNS.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE bets ADD COLUMN {name} {definition}")


def _load_csv(conn, data_dir):
    with open(data_dir / "assets.csv", newline="") as f:
        conn.executemany(
            "INSERT INTO assets (symbol, name, category, pip_size) "
            "VALUES (:symbol, :name, :category, :pip_size)",
            csv.DictReader(f),
        )
    with open(data_dir / "prices.csv", newline="") as f:
        conn.executemany(
            "INSERT INTO prices (symbol, date, close) "
            "VALUES (:symbol, :date, :close)",
            csv.DictReader(f),
        )
