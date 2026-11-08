"""Integration tests: drive the real Flask routes and SQLite database."""
import re
import sqlite3

BET = {"player_name": "Enzo", "symbol": "^GSPC", "direction": "buy",
       "stake": "100", "entry_date": "2020-03-23", "exit_date": "2020-12-31"}


def test_database_is_loaded_from_csv(app):
    conn = sqlite3.connect(app.config["DATABASE"])
    assert conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 10
    assert conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0] > 25000


def test_all_pages_load(client):
    for path in ("/", "/history", "/leaderboard"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"Skip to main content" in response.data


def test_form_fields_have_labels(client):
    html = client.get("/").get_data(as_text=True)
    for field in ("player_name", "symbol", "buy", "sell", "entry_date",
                  "exit_date", "stake", "stop_loss"):
        assert f'for="{field}"' in html and f'id="{field}"' in html


def test_winning_bet_is_settled_and_saved(client, app):
    # Buying the S&P 500 at the March 2020 low was a big winner.
    response = client.post("/bet", data=BET, follow_redirects=True)
    html = response.get_data(as_text=True)
    assert "Winner" in html and "You made $" in html

    row = sqlite3.connect(app.config["DATABASE"]).execute(
        "SELECT direction, profit, entry_date FROM bets").fetchone()
    assert row[0] == "buy" and row[1] > 50 and row[2] == "2020-03-23"


def test_weekend_dates_snap_to_trading_days(client, app):
    # 2020-03-21 is a Saturday: the bet should enter on Monday the 23rd.
    client.post("/bet", data={**BET, "entry_date": "2020-03-21"})
    row = sqlite3.connect(app.config["DATABASE"]).execute(
        "SELECT entry_date FROM bets").fetchone()
    assert row[0] == "2020-03-23"


def test_invalid_bet_shows_error_and_saves_nothing(client, app):
    response = client.post("/bet", data={**BET, "stake": "-1"},
                           follow_redirects=True)
    assert b"role=\"alert\"" in response.data
    assert b"more than $0" in response.data
    count = sqlite3.connect(app.config["DATABASE"]).execute(
        "SELECT COUNT(*) FROM bets").fetchone()[0]
    assert count == 0


def test_history_and_leaderboard_show_bets(client):
    client.post("/bet", data=BET)
    client.post("/bet", data={**BET, "direction": "sell"})
    history = client.get("/history").get_data(as_text=True)
    assert "Win rate" in history and "50%" in history
    board = client.get("/leaderboard").get_data(as_text=True)
    assert "Enzo" in board and "(you)" in board


def test_player_names_are_case_insensitive(client, app):
    client.post("/bet", data=BET)
    client.post("/bet", data={**BET, "player_name": "ENZO"})
    players = sqlite3.connect(app.config["DATABASE"]).execute(
        "SELECT COUNT(*) FROM players").fetchone()[0]
    assert players == 1


def test_missing_bet_returns_404(client):
    assert client.get("/bet/999").status_code == 404


def test_break_even_bet_is_not_called_a_loss(client, app):
    # Real prices rarely close exactly level, so store a zero-profit bet directly.
    client.post("/bet", data=BET)
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.execute("UPDATE bets SET exit_price = entry_price, pips = 0, profit = 0")
    conn.commit()
    html = client.get("/bet/1").get_data(as_text=True)
    assert "You broke even" in html
    assert "Busted" not in html and "You lost" not in html


def test_prices_keep_their_decimal_places(client):
    # EUR/USD is quoted to 4 decimals (one pip = 0.0001), even when it ends in 0.
    client.post("/bet", data={**BET, "symbol": "EURUSD=X"})
    html = client.get("/bet/1").get_data(as_text=True)
    assert re.search(r"2020-03-23 at 1\.\d{4}<", html)
    client.post("/bet", data=BET)
    html = client.get("/bet/2").get_data(as_text=True)
    assert re.search(r"2020-03-23 at 2,\d{3}\.\d{2}<", html)


def test_stop_loss_closes_a_bet_early(client, app):
    # Buying the S&P 500 at its February 2020 peak: held to December it wins,
    # but a 10% stop closes it in the late-February crash.
    peak = {**BET, "entry_date": "2020-02-19", "stop_loss": "10"}
    html = client.post("/bet", data=peak, follow_redirects=True).get_data(
        as_text=True)
    assert "Stopped out" in html and "planned exit 2020-12-31" in html

    row = sqlite3.connect(app.config["DATABASE"]).execute(
        "SELECT exit_date, profit, stop_loss, stopped_out FROM bets").fetchone()
    # The stop is checked at each close, and the S&P 500 fell 4.4% on
    # 2020-02-27, jumping from about -8% straight past the stop to -12%.
    assert row[0] == "2020-02-27"
    assert -13 < row[1] <= -10 and row[2] == 10 and row[3] == 1

    history = client.get("/history").get_data(as_text=True)
    assert "stopped" in history


def test_bet_without_stop_loss_runs_to_exit(client, app):
    client.post("/bet", data={**BET, "entry_date": "2020-02-19"})
    row = sqlite3.connect(app.config["DATABASE"]).execute(
        "SELECT exit_date, profit, stop_loss, stopped_out FROM bets").fetchone()
    assert row == ("2020-12-31", row[1], None, 0) and row[1] > 0


def test_week_9_database_gets_new_columns(tmp_path):
    # A database saved by the Week 9 version (no stop loss columns) must keep
    # its bets and gain the new columns when the new version starts.
    from app import create_app
    database = tmp_path / "old.db"
    conn = sqlite3.connect(database)
    conn.executescript("""
        CREATE TABLE bets (id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL, symbol TEXT NOT NULL,
            direction TEXT NOT NULL, stake REAL NOT NULL,
            entry_date TEXT NOT NULL, exit_date TEXT NOT NULL,
            entry_price REAL NOT NULL, exit_price REAL NOT NULL,
            pips REAL NOT NULL, profit REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        INSERT INTO bets (player_id, symbol, direction, stake, entry_date,
            exit_date, entry_price, exit_price, pips, profit)
        VALUES (1, '^GSPC', 'buy', 100, '2020-01-02', '2020-12-31',
                3257.85, 3756.07, 498.2, 15.29);
    """)
    conn.commit()
    conn.close()

    create_app({"TESTING": True, "DATABASE": str(database)})
    conn = sqlite3.connect(database)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(bets)")}
    assert {"stop_loss", "stopped_out", "planned_exit_date"} <= columns
    assert conn.execute("SELECT profit, stopped_out FROM bets").fetchone() == (15.29, 0)


def _close(app, symbol, day):
    return sqlite3.connect(app.config["DATABASE"]).execute(
        "SELECT close FROM prices WHERE symbol = ? AND date = ?",
        (symbol, day)).fetchone()[0]


def test_benchmark_defaults_to_sp500(client, app):
    client.post("/bet", data={**BET, "symbol": "GC=F"})
    html = client.get("/bet/1").get_data(as_text=True)
    assert "Did you beat the market?" in html
    assert 'for="vs"' in html and 'id="vs"' in html
    assert "Buy and hold S&amp;P 500" in html
    # The same $100 in the S&P 500 over the bet's dates.
    expected = 100 * (_close(app, "^GSPC", "2020-12-31")
                      / _close(app, "^GSPC", "2020-03-23") - 1)
    assert f"{expected:+.2f}" in html


def test_player_picks_benchmark_market(client, app):
    client.post("/bet", data=BET)
    html = client.get("/bet/1?vs=BTC-USD").get_data(as_text=True)
    assert "Buy and hold Bitcoin" in html
    assert '<option value="BTC-USD" selected>' in html
    # Bitcoin more than tripled from March to December 2020.
    assert "Bitcoin beat your bet by $" in html


def test_bet_on_sp500_is_not_compared_with_itself(client):
    client.post("/bet", data=BET)  # an S&P 500 bet
    html = client.get("/bet/1?vs=%5EGSPC").get_data(as_text=True)
    assert "Buy and hold Gold" in html
    assert 'value="^GSPC"' not in html  # not offered in the dropdown


def test_unknown_benchmark_falls_back_to_default(client):
    client.post("/bet", data={**BET, "symbol": "GC=F"})
    response = client.get("/bet/1?vs=NOPE")
    assert response.status_code == 200
    assert "Buy and hold S&amp;P 500" in response.get_data(as_text=True)


def test_benchmark_without_trading_days_says_so(client):
    # A weekend Bitcoin bet: the S&P 500 did not trade that Saturday or Sunday.
    client.post("/bet", data={**BET, "symbol": "BTC-USD",
                              "entry_date": "2020-03-21",
                              "exit_date": "2020-03-22"})
    html = client.get("/bet/1").get_data(as_text=True)
    assert "S&amp;P 500 did not trade between" in html


def test_result_and_history_have_accessible_charts(client):
    client.post("/bet", data={**BET, "stop_loss": "50"})
    result = client.get("/bet/1").get_data(as_text=True)
    assert 'role="img"' in result and "<polyline" in result
    assert "S&amp;P 500 closing price, 2020-03-23 to 2020-12-31" in result
    assert "Stop 1," in result  # the 50% stop is drawn and labelled

    history = client.get("/history").get_data(as_text=True)
    assert 'role="img"' in history
    assert "Running total profit after each bet" in history
