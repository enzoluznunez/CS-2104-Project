"""Integration tests: drive the real Flask routes and SQLite database."""
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
                  "exit_date", "stake"):
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
