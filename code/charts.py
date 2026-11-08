"""Server-drawn line charts.

Python works out where everything goes and templates/_chart.html draws it as
inline SVG, so the charts need no JavaScript and work offline in the
container. Each chart also gets a plain-text summary for screen readers.
"""
import math

MAX_POINTS = 400  # long price histories are thinned to keep the page small


def nice_step(rough):
    """Round a gridline spacing to 1, 2 or 5 times a power of ten."""
    power = 10 ** math.floor(math.log10(rough))
    for multiple in (1, 2, 5, 10):
        if rough <= multiple * power:
            return multiple * power
    return 10 * power  # not reached; keeps linters happy


class LineChart:
    """Coordinates for one line chart in an SVG viewBox of width x height.

    values are the y values in order and labels name each point on the x
    axis. extra lists y values that must fit on the chart even though they
    are not on the line (e.g. the stop loss price, or zero).
    money=True labels the y axis in dollars with a sign (+$50, -$20).
    """

    width, height = 640, 260
    left, right, top, bottom = 84, 20, 18, 36

    def __init__(self, values, labels, extra=(), money=False):
        if not values:
            raise ValueError("A chart needs at least one value.")
        self.values, self.labels, self.money = list(values), list(labels), money

        low, high = min(self.values + list(extra)), max(self.values + list(extra))
        if low == high:  # a flat line still needs some height
            low, high = low - 1, high + 1
        self.step = nice_step((high - low) / 4)
        self.low = math.floor(low / self.step) * self.step
        self.high = math.ceil(high / self.step) * self.step

    @property
    def plot_right(self):
        return self.width - self.right

    @property
    def plot_bottom(self):
        return self.height - self.bottom

    def x(self, index):
        if len(self.values) == 1:
            return round((self.left + self.plot_right) / 2, 1)
        share = index / (len(self.values) - 1)
        return round(self.left + share * (self.plot_right - self.left), 1)

    def y(self, value):
        share = (self.high - value) / (self.high - self.low)
        return round(self.top + share * (self.plot_bottom - self.top), 1)

    def point(self, index):
        return self.x(index), self.y(self.values[index])

    @property
    def points(self):
        """The line as an SVG polyline "x,y x,y ..." string, thinned if long."""
        count = len(self.values)
        stride = max(1, math.ceil(count / MAX_POINTS))
        indexes = list(range(0, count, stride))
        if indexes[-1] != count - 1:
            indexes.append(count - 1)  # always end on the real last point
        return " ".join(f"{self.x(i)},{self.y(self.values[i])}" for i in indexes)

    @property
    def y_ticks(self):
        """(y position, label) for each horizontal gridline."""
        decimals = max(0, -math.floor(math.log10(self.step)))
        count = round((self.high - self.low) / self.step)
        ticks = []
        for k in range(count + 1):
            value = round(self.low + k * self.step, decimals)
            ticks.append((self.y(value), self._label(value, decimals)))
        return ticks

    @property
    def x_ticks(self):
        """(x position, label, text-anchor) for the first, middle and last point."""
        last = len(self.values) - 1
        chosen = sorted({0, last // 2, last})
        anchors = {0: "start", last: "end"}
        return [(self.x(i), self.labels[i], anchors.get(i, "middle"))
                for i in chosen]

    def _label(self, value, decimals):
        if not self.money:
            return f"{value:,.{decimals}f}"
        sign = "+" if value > 0 else "-" if value < 0 else ""
        return f"{sign}${abs(value):,.{decimals}f}"


def price_chart(path, entry_price, direction, stop_loss=None):
    """Chart of a market's closing prices over a bet, with the stop marked."""
    stop_price = None
    if stop_loss is not None:
        sign = 1 if direction == "buy" else -1
        stop_price = entry_price * (1 - sign * stop_loss / 100)
    chart = LineChart([day["close"] for day in path],
                      [day["date"] for day in path],
                      extra=[stop_price] if stop_price is not None else ())
    chart.stop_price = stop_price
    low = min(range(len(path)), key=lambda i: path[i]["close"])
    high = max(range(len(path)), key=lambda i: path[i]["close"])
    chart.low_day, chart.high_day = path[low], path[high]
    return chart


def running_total_chart(bets):
    """Chart of a player's running total profit after each bet, oldest first."""
    totals, total = [0.0], 0.0
    for bet in bets:
        total = round(total + bet["profit"], 2)
        totals.append(total)
    labels = ["Start"] + [f"Bet {n}" for n in range(1, len(bets) + 1)]
    chart = LineChart(totals, labels, extra=[0], money=True)
    peak = max(range(len(totals)), key=lambda i: totals[i])
    trough = min(range(len(totals)), key=lambda i: totals[i])
    chart.summary = {"final": totals[-1], "count": len(bets),
                     "peak": totals[peak], "peak_label": labels[peak],
                     "trough": totals[trough], "trough_label": labels[trough]}
    return chart
