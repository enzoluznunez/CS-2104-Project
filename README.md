# Seeking Pips

Seeking Pips is a betting game played on market history. Pick a market (S&P 500,
gold, EUR/USD, Bitcoin and more), choose **Buy** if you think the price went up
or **Sell** if you think it went down, then set an entry date, an exit date and
a stake. The site settles the bet straight away against real 2015–2025 closing
prices and tells you whether you won or lost, by how much, and how many pips
the market moved.

![Place a bet page](docs/index.png)

## Pages

| Page | URL | What it does |
| --- | --- | --- |
| Place a Bet | `/` | Form to pick a player name, market, direction, dates and stake |
| Bet Result | `/bet/<id>` | Win/loss, profit, percent move and pips for one bet |
| My Bets | `/history` | Your win rate, net result, best/worst bet and a table of every bet |
| Leaderboard | `/leaderboard` | Top 25 players ranked by total profit |

## What is stored in the database

SQLite (`instance/seeking_pips.db`, schema in `code/schema.sql`) holds four tables:

- **assets**: the 10 tradable markets and their pip size (e.g. 0.0001 for EUR/USD)
- **prices**: about 29,000 daily closing prices, loaded from `data/prices.csv` on first start
- **players**: everyone who has placed a bet (names are case-insensitive)
- **bets**: every bet placed, with entry/exit prices, pips and profit

## How a bet is settled

1. The entry date moves forward to the first trading day on or after it, and the
   exit date moves back to the last trading day on or before it (markets are
   closed on weekends and holidays).
2. `profit = stake × (exit − entry) / entry`, negated for a Sell.
3. `pips = (exit − entry) / pip_size`, also negated for a Sell.

The logic lives in `code/betting.py`.

## Repository layout

```
code/       Flask app (app.py), database helpers (db.py), bet logic (betting.py),
            schema.sql, templates/ (HTML) and static/ (CSS)
data/       assets.csv, prices.csv and fetch_prices.py, which downloads them
tests/      pytest unit and integration tests, plus test_results.txt
docs/       Screenshots
report/     Final report (Week 10)
Dockerfile  Container image definition
```

## Running it in a container (recommended)

Requires [Docker](https://www.docker.com/).

```bash
git clone <this repository URL> seeking-pips
cd seeking-pips
docker build -t seeking-pips .
docker run -d --name seeking-pips -p 8000:5000 \
    -v seeking-pips-data:/app/instance seeking-pips
```

Open <http://localhost:8000>. The app listens on port 5000 inside the container.
It is mapped to 8000 on the host because macOS uses port 5000 for AirPlay.

The `-v seeking-pips-data:/app/instance` volume keeps players and bets when the
container is removed and started again. Useful commands:

```bash
docker logs seeking-pips              # view server logs
docker exec seeking-pips python -m pytest -v   # run the tests in the container
docker rm -f seeking-pips             # stop and remove the container
docker volume rm seeking-pips-data    # wipe all players and bets
```

Set `SECRET_KEY` to a random value outside local testing, for example
`docker run -e SECRET_KEY=... ...`.

## Running it without Docker

Requires Python 3.12 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python code/app.py        # development server at http://localhost:5000
```

## Reproducing results

- **Tests:** `python -m pytest -v` runs 22 unit and integration tests. They cover
  bet math, input validation, weekend date handling, database loading, form
  labels and the full bet → history → leaderboard flow. The output of a run
  inside the container is saved in `tests/test_results.txt`.
- **Price data:** `pip install yfinance pandas && python data/fetch_prices.py`
  downloads `data/prices.csv` again from Yahoo Finance. The site itself never
  needs network access.
- **Example bet:** a $250 Buy on Bitcoin from 2020-01-01 to 2021-01-01 wins
  $769.91 (+308%).

## Accessibility

- Every form control has a visible `<label>`. Buy/Sell is a real radio group in a
  `<fieldset>` with a `<legend>`.
- Everything works by keyboard: a skip link, a visible focus ring on all
  controls, and `aria-current` on the current page in the navigation.
- Errors are announced with `role="alert"`. Win and loss are spelled out in words
  and symbols, not shown by colour alone.
- Tables have captions and header scopes. Colours meet WCAG AA contrast, and
  animations are turned off for `prefers-reduced-motion`.

## Technologies

- **Python 3.12** with **Flask 3.1** (web framework) and **gunicorn** (production server)
- **SQLite** (built into Python) for storage
- **HTML** with Jinja2 templates, and hand-written **CSS** (no frameworks)
- **pytest** for testing
- **Docker** for the container
- **yfinance** (data preparation only) for Yahoo Finance prices

## Roadmap (Week 10)

- Flagship feature: a **benchmark**. Each bet is compared against what the same
  stake would have earned in a simple buy-and-hold of the S&P 500 over the same
  dates.
- Deploy the container on Discovery.

## Author

**Enzo Nunez** (enzonunez@vt.edu): project idea, design, implementation,
testing and documentation. Claude (Anthropic) was used as a coding assistant;
see the LLM statement in the submission.
