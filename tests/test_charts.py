# Seeking Pips | Enzo Nunez (enzonunez) | CS 2104, section 83521
# Honor code: As a Hokie, I will conduct myself with honor and integrity at
#   all times. I will not lie, cheat, or steal, nor will I accept the actions
#   of those who do.
# LLM use: I used Claude Code by Anthropic for code generation and debugging.

"""Unit tests for the server-drawn SVG charts in code/charts.py."""
import pytest

from charts import LineChart, nice_step, price_chart, running_total_chart


@pytest.mark.parametrize("rough, step", [
    (0.7, 1), (1.5, 2), (3, 5), (7, 10), (130, 200), (0.00031, 0.0005),
])
def test_nice_step_rounds_to_1_2_or_5(rough, step):
    assert nice_step(rough) == pytest.approx(step)


def test_line_fills_the_plot_area():
    chart = LineChart([10, 20, 30], ["a", "b", "c"])
    first, last = chart.point(0), chart.point(2)
    assert first[0] == chart.left and last[0] == chart.plot_right
    # Higher values are drawn higher up (smaller y in SVG).
    assert last[1] < first[1]
    assert chart.top <= last[1] and first[1] <= chart.plot_bottom


def test_gridlines_cover_every_value():
    chart = LineChart([3.2, 4.9], ["a", "b"], extra=[0])
    assert chart.low <= 0 and chart.high >= 4.9
    # A 0-4.9 range in about four steps gives gridlines every 2.
    assert [label for _, label in chart.y_ticks] == ["0", "2", "4", "6"]


def test_flat_line_still_gets_a_scale():
    chart = LineChart([5, 5], ["a", "b"])
    assert chart.low < 5 < chart.high


def test_long_series_is_thinned_but_keeps_its_ends():
    values = list(range(4000))
    chart = LineChart(values, [str(v) for v in values])
    points = chart.points.split()
    assert len(points) <= 401
    assert points[0] == "{},{}".format(*chart.point(0))
    assert points[-1] == "{},{}".format(*chart.point(3999))


def test_price_chart_marks_stop_and_extremes():
    path = [{"date": "d1", "close": 100}, {"date": "d2", "close": 95},
            {"date": "d3", "close": 105}]
    chart = price_chart(path, 100, "buy", stop_loss=20)
    assert chart.stop_price == 80 and chart.low <= 80  # stop is on the chart
    assert chart.low_day["date"] == "d2" and chart.high_day["date"] == "d3"
    assert price_chart(path, 100, "sell", stop_loss=20).stop_price == 120
    assert price_chart(path, 100, "buy").stop_price is None


def test_running_total_chart_starts_at_zero():
    chart = running_total_chart([{"profit": 10}, {"profit": -30},
                                 {"profit": 5.5}])
    assert chart.values == [0, 10, -20, -14.5]
    assert chart.labels[0] == "Start" and chart.labels[-1] == "Bet 3"
    assert chart.summary["peak"] == 10 and chart.summary["peak_label"] == "Bet 1"
    assert chart.summary["trough"] == -20
    assert [label for _, label in chart.y_ticks][0].startswith("-$")
