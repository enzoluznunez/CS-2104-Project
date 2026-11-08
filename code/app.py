"""Seeking Pips: bet on what markets already did."""
import math
import os
from pathlib import Path

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

import db
from betting import BetError, find_prices, parse_bet, settle

ROOT_DIR = Path(__file__).resolve().parent.parent


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        # Override both in production with environment variables.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get("DATABASE",
                                str(ROOT_DIR / "instance" / "seeking_pips.db")),
        DATA_DIR=str(ROOT_DIR / "data"),
    )
    if config:
        app.config.update(config)

    db.init_db(app.config["DATABASE"], app.config["DATA_DIR"])
    app.teardown_appcontext(db.close_db)

    @app.template_filter("price")
    def format_price(value, pip_size):
        # Show at least as many decimals as one pip, so EUR/USD prints
        # 1.1000 rather than 1.1, and never fewer than two (3,234.85).
        decimals = max(2, round(-math.log10(pip_size)))
        return f"{value:,.{decimals}f}"

    @app.context_processor
    def inject_player():
        # Every template can show who is playing without each route passing it.
        return {"player_name": session.get("player_name")}

    @app.get("/")
    def index():
        conn = db.get_db()
        assets = conn.execute(
            "SELECT symbol, name, category FROM assets ORDER BY category, name"
        ).fetchall()
        first, last = conn.execute(
            "SELECT MIN(date), MAX(date) FROM prices").fetchone()
        return render_template("index.html", assets=assets, first=first,
                               last=last, form=request.args)

    @app.post("/bet")
    def place_bet():
        name = request.form.get("player_name", "").strip()
        try:
            if not 1 <= len(name) <= 30:
                raise BetError("Enter a player name of 1 to 30 characters.")
            bet = parse_bet(request.form)
            conn = db.get_db()
            asset = conn.execute("SELECT * FROM assets WHERE symbol = ?",
                                 (bet["symbol"],)).fetchone()
            if asset is None:
                raise BetError("That asset is not available.")
            entry, exit_ = find_prices(conn, bet["symbol"], bet["entry_date"],
                                       bet["exit_date"])
        except BetError as error:
            flash(str(error), "error")
            # Send the user back with what they typed so they can fix it.
            return redirect(url_for("index", **request.form))

        result = settle(bet["direction"], bet["stake"], entry["close"],
                        exit_["close"], asset["pip_size"])
        player_id = _get_or_create_player(conn, name)
        cursor = conn.execute(
            "INSERT INTO bets (player_id, symbol, direction, stake, entry_date,"
            " exit_date, entry_price, exit_price, pips, profit)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (player_id, bet["symbol"], bet["direction"], bet["stake"],
             entry["date"], exit_["date"], entry["close"], exit_["close"],
             result["pips"], result["profit"]))
        conn.commit()
        session["player_name"] = name
        return redirect(url_for("bet_result", bet_id=cursor.lastrowid))

    @app.get("/bet/<int:bet_id>")
    def bet_result(bet_id):
        bet = db.get_db().execute(
            "SELECT bets.*, assets.name AS asset_name, assets.pip_size,"
            " players.name AS player"
            " FROM bets JOIN assets USING (symbol)"
            " JOIN players ON players.id = bets.player_id"
            " WHERE bets.id = ?", (bet_id,)).fetchone()
        if bet is None:
            abort(404)
        percent = round(bet["profit"] / bet["stake"] * 100, 2)
        return render_template("result.html", bet=bet, percent=percent)

    @app.get("/history")
    def history():
        name = session.get("player_name")
        bets, summary = [], None
        if name:
            conn = db.get_db()
            bets = conn.execute(
                "SELECT bets.*, assets.name AS asset_name FROM bets"
                " JOIN assets USING (symbol)"
                " JOIN players ON players.id = bets.player_id"
                " WHERE players.name = ? ORDER BY bets.id DESC",
                (name,)).fetchall()
            summary = _summarize(bets)
        return render_template("history.html", bets=bets, summary=summary)

    @app.get("/leaderboard")
    def leaderboard():
        rows = db.get_db().execute(
            "SELECT players.name, COUNT(*) AS bets,"
            " SUM(profit > 0) AS wins, ROUND(SUM(profit), 2) AS total"
            " FROM bets JOIN players ON players.id = bets.player_id"
            " GROUP BY players.id ORDER BY total DESC LIMIT 25").fetchall()
        return render_template("leaderboard.html", rows=rows)

    @app.post("/sign-out")
    def sign_out():
        session.pop("player_name", None)
        flash("You switched players. Enter a new name with your next bet.",
              "info")
        return redirect(url_for("index"))

    return app


def _get_or_create_player(conn, name):
    # Names are case-insensitive (see schema), so "Enzo" and "enzo" match.
    conn.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
    return conn.execute("SELECT id FROM players WHERE name = ?",
                        (name,)).fetchone()["id"]


def _summarize(bets):
    if not bets:
        return None
    wins = sum(1 for bet in bets if bet["profit"] > 0)
    return {
        "count": len(bets),
        "wins": wins,
        "win_rate": round(wins / len(bets) * 100),
        "total": round(sum(bet["profit"] for bet in bets), 2),
        "best": max(bet["profit"] for bet in bets),
        "worst": min(bet["profit"] for bet in bets),
    }


if __name__ == "__main__":
    # Development only. The debugger can run code, so it stays on localhost;
    # the container uses gunicorn instead (see Dockerfile).
    create_app().run(host="127.0.0.1",
                     port=int(os.environ.get("PORT", 5000)), debug=True)
