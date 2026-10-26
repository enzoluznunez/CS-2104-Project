"""Core betting logic: validate a bet and settle it against historical prices."""
from datetime import date

MAX_STAKE = 1_000_000


class BetError(ValueError):
    """A bet the user entered that cannot be placed; the message is shown."""


def settle(direction, stake, entry_price, exit_price, pip_size):
    """Work out how a bet would have turned out.

    A "buy" wins when the price rises and a "sell" wins when it falls. The
    stake is treated as money invested at the entry price, so profit scales
    with the percentage move, and pips measure the move in the asset's own
    units (e.g. 0.0001 for EUR/USD, 1 point for the S&P 500).
    """
    sign = 1 if direction == "buy" else -1
    change = (exit_price - entry_price) / entry_price
    return {
        "pips": round(sign * (exit_price - entry_price) / pip_size, 1),
        "profit": round(sign * stake * change, 2),
        "percent": round(sign * change * 100, 2),
    }


def parse_bet(form):
    """Check the submitted form and return clean values, or raise BetError."""
    symbol = form.get("symbol", "").strip()
    if not symbol:
        raise BetError("Pick an asset to bet on.")

    direction = form.get("direction", "")
    if direction not in ("buy", "sell"):
        raise BetError("Choose whether you are buying or selling.")

    try:
        stake = round(float(form.get("stake", "")), 2)
    except ValueError:
        raise BetError("Enter your stake as a number, like 100.") from None
    if not 0 < stake <= MAX_STAKE:
        raise BetError(f"Stake must be more than $0 and at most ${MAX_STAKE:,}.")

    try:
        entry = date.fromisoformat(form.get("entry_date", ""))
        exit_ = date.fromisoformat(form.get("exit_date", ""))
    except ValueError:
        raise BetError("Enter both dates as year-month-day.") from None
    if exit_ <= entry:
        raise BetError("The exit date must be after the entry date.")

    return {"symbol": symbol, "direction": direction, "stake": stake,
            "entry_date": entry.isoformat(), "exit_date": exit_.isoformat()}


def find_prices(db, symbol, entry_date, exit_date):
    """Look up the closing prices used to settle a bet.

    Markets are closed on weekends and holidays, so the bet enters on the
    first trading day on or after entry_date and exits on the last trading
    day on or before exit_date.
    """
    entry = db.execute(
        "SELECT date, close FROM prices WHERE symbol = ? AND date >= ? "
        "ORDER BY date LIMIT 1", (symbol, entry_date)).fetchone()
    exit_ = db.execute(
        "SELECT date, close FROM prices WHERE symbol = ? AND date <= ? "
        "ORDER BY date DESC LIMIT 1", (symbol, exit_date)).fetchone()
    if entry is None or exit_ is None or exit_["date"] <= entry["date"]:
        raise BetError("There is no trading data for those dates. "
                       "Try a wider date range.")
    return entry, exit_
