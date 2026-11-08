# Seeking Pips | Enzo Nunez (enzonunez) | CS 2104, section 83521
# Honor code: As a Hokie, I will conduct myself with honor and integrity at
#   all times. I will not lie, cheat, or steal, nor will I accept the actions
#   of those who do.
# LLM use: I used Claude Code by Anthropic for code generation and debugging.

"""Seeking Pips: bet on what markets already did."""
import math
import os
from pathlib import Path

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

import db
from charts import price_chart, running_total_chart
from betting import (BetError, benchmark, find_prices, find_stop_out,
                     parse_bet, price_path, settle)

ROOT_DIR = Path(__file__).resolve().parent.parent

# The market a bet is compared against until the player picks another one.
# A bet on the S&P 500 itself is compared against gold instead.
DEFAULT_BENCHMARK = "^GSPC"
FALLBACK_BENCHMARK = "GC=F"


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

        planned_exit = exit_["date"]
        stop_day = None
        if bet["stop_loss"] is not None:
            path = price_path(conn, bet["symbol"], entry["date"], exit_["date"])
            stop_day = find_stop_out(path, bet["direction"], entry["close"],
                                     bet["stop_loss"])
            if stop_day is not None:
                exit_ = stop_day  # the stop closed the bet early

        result = settle(bet["direction"], bet["stake"], entry["close"],
                        exit_["close"], asset["pip_size"])
        player_id = _get_or_create_player(conn, name)
        cursor = conn.execute(
            "INSERT INTO bets (player_id, symbol, direction, stake, entry_date,"
            " exit_date, entry_price, exit_price, pips, profit, stop_loss,"
            " stopped_out, planned_exit_date)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (player_id, bet["symbol"], bet["direction"], bet["stake"],
             entry["date"], exit_["date"], entry["close"], exit_["close"],
             result["pips"], result["profit"], bet["stop_loss"],
             int(stop_day is not None), planned_exit))
        conn.commit()
        session["player_name"] = name
        return redirect(url_for("bet_result", bet_id=cursor.lastrowid))

    @app.get("/bet/<int:bet_id>")
    def bet_result(bet_id):
        conn = db.get_db()
        bet = conn.execute(
            "SELECT bets.*, assets.name AS asset_name, assets.pip_size,"
            " players.name AS player"
            " FROM bets JOIN assets USING (symbol)"
            " JOIN players ON players.id = bets.player_id"
            " WHERE bets.id = ?", (bet_id,)).fetchone()
        if bet is None:
            abort(404)
        percent = round(bet["profit"] / bet["stake"] * 100, 2)

        # Benchmark: the player picks any other market (?vs=SYMBOL) and sees
        # what buying and holding it over the bet's real dates would have made.
        others = conn.execute(
            "SELECT symbol, name, category FROM assets WHERE symbol != ?"
            " ORDER BY category, name", (bet["symbol"],)).fetchall()
        names = {asset["symbol"]: asset["name"] for asset in others}
        vs = request.args.get("vs")
        if vs not in names:  # missing, unknown or the bet's own market
            vs = (DEFAULT_BENCHMARK if DEFAULT_BENCHMARK in names
                  else FALLBACK_BENCHMARK)
        compare = benchmark(conn, vs, bet["entry_date"], bet["exit_date"],
                            bet["stake"])

        chart = price_chart(
            price_path(conn, bet["symbol"], bet["entry_date"], bet["exit_date"]),
            bet["entry_price"], bet["direction"], bet["stop_loss"])
        return render_template("result.html", bet=bet, percent=percent,
                               others=others, vs=vs, vs_name=names[vs],
                               compare=compare, chart=chart)

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
        # bets are newest first for the table; the chart runs oldest first.
        chart = running_total_chart(bets[::-1]) if bets else None
        return render_template("history.html", bets=bets, summary=summary,
                               chart=chart)

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
