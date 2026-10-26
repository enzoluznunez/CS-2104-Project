"""Unit tests for the pure bet logic in code/betting.py."""
import re

import pytest

from betting import BetError, parse_bet, settle

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
])
def test_parse_bet_rejects_bad_input(field, value, message):
    with pytest.raises(BetError, match=re.escape(message)):
        parse_bet({**VALID, field: value})
