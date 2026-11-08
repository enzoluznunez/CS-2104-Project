# Seeking Pips | Enzo Nunez (enzonunez) | CS 2104, section 83521
# Honor code: As a Hokie, I will conduct myself with honor and integrity at
#   all times. I will not lie, cheat, or steal, nor will I accept the actions
#   of those who do.
# LLM use: I used Claude Code by Anthropic for code generation and debugging.

"""Unit tests for the pure bet logic in code/betting.py."""
import re

import pytest

from betting import BetError, find_stop_out, parse_bet, settle

VALID = {"symbol": "^GSPC", "direction": "buy", "stake": "100",
         "entry_date": "2020-01-02", "exit_date": "2020-12-31"}


def test_buy_wins_when_price_rises():
    result = settle("buy", 100, 50.0, 55.0, pip_size=1)
    assert result == {"pips": 5.0, "profit": 10.0, "percent": 10.0}


def test_sell_wins_when_price_falls():
    result = settle("sell", 200, 1.2000, 1.1900, pip_size=0.0001)
    assert result["pips"] == 100.0
    assert result["profit"] == pytest.approx(1.67, abs=0.01)


def test_buy_loses_when_price_falls():
    assert settle("buy", 100, 100.0, 90.0, pip_size=1)["profit"] == -10.0


def test_parse_bet_accepts_valid_form():
    bet = parse_bet(VALID)
    assert bet["stake"] == 100.0 and bet["direction"] == "buy"


@pytest.mark.parametrize("field, value, message", [
    ("symbol", "", "Pick an asset"),
    ("direction", "hold", "buying or selling"),
    ("stake", "lots", "as a number"),
    ("stake", "0", "more than $0"),
    ("stake", "-5", "more than $0"),
    ("stake", "2000000", "at most"),
    ("entry_date", "not-a-date", "year-month-day"),
    ("exit_date", "2019-01-01", "after the entry date"),
    ("exit_date", "2020-01-02", "after the entry date"),
    ("stop_loss", "ten", "as a percentage"),
    ("stop_loss", "0", "more than 0%"),
    ("stop_loss", "150", "at most 100%"),
])
def test_parse_bet_rejects_bad_input(field, value, message):
    with pytest.raises(BetError, match=re.escape(message)):
        parse_bet({**VALID, field: value})


def test_stop_loss_is_optional():
    assert parse_bet(VALID)["stop_loss"] is None
    assert parse_bet({**VALID, "stop_loss": " "})["stop_loss"] is None
    assert parse_bet({**VALID, "stop_loss": "12.5"})["stop_loss"] == 12.5


def _path(*closes):
    return [{"date": f"2020-01-{day:02d}", "close": close}
            for day, close in enumerate(closes, start=1)]


def test_buy_stop_triggers_on_first_close_past_the_stop():
    # Down 5%, then 10% (exactly at the stop), then 20%.
    day = find_stop_out(_path(100, 95, 90, 80), "buy", 100, stop_loss=10)
    assert day["date"] == "2020-01-03"


def test_sell_stop_triggers_when_price_rises():
    day = find_stop_out(_path(100, 104, 112, 90), "sell", 100, stop_loss=10)
    assert day["date"] == "2020-01-03"


def test_stop_not_triggered_when_loss_stays_small():
    assert find_stop_out(_path(100, 95, 92, 120), "buy", 100, 10) is None
    # A big gain is not a loss for a buy...
    assert find_stop_out(_path(100, 150), "buy", 100, 10) is None
