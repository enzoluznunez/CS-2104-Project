# Seeking Pips | Enzo Nunez (enzonunez) | CS 2104, section 83521
# Honor code: As a Hokie, I will conduct myself with honor and integrity at
#   all times. I will not lie, cheat, or steal, nor will I accept the actions
#   of those who do.
# LLM use: I used Claude Code by Anthropic for code generation and debugging.

"""Download daily closing prices for every asset in assets.csv.

This is a one-time data preparation step, run on a developer machine:

    pip install yfinance pandas
    python data/fetch_prices.py

The output (data/prices.csv) is committed to the repository so the website
and its container never need network access to Yahoo Finance at runtime.
"""
import csv
from pathlib import Path

import yfinance as yf

DATA_DIR = Path(__file__).resolve().parent
START, END = "2015-01-01", "2026-01-01"


def main():
    with open(DATA_DIR / "assets.csv", newline="") as f:
        symbols = [row["symbol"] for row in csv.DictReader(f)]

    rows = []
    for symbol in symbols:
        frame = yf.download(symbol, start=START, end=END, progress=False,
                            auto_adjust=False)
        # yfinance returns a column per ticker; take the single Close series.
        closes = frame["Close"][symbol].dropna()
        for day, close in closes.items():
            rows.append((symbol, day.strftime("%Y-%m-%d"), round(float(close), 6)))
        print(f"{symbol}: {len(closes)} days")

    with open(DATA_DIR / "prices.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "date", "close"])
        writer.writerows(rows)


if __name__ == "__main__":
    main()
