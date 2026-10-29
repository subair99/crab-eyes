import math

from app.tools.calculator import annualise, describe, fails

T = {"maths": {"max_plausible_annual_return": 1.0, "benchmark_multiple": 3.0}}


def test_thirty_percent_monthly_is_about_2230_percent_a_year():
    assert math.isclose(annualise(0.30, 1), 22.298, rel_tol=1e-3)


def test_forty_percent_monthly_is_about_5569_percent_a_year():
    assert math.isclose(annualise(0.40, 1), 55.693, rel_tol=1e-3)


def test_doubling_in_a_month():
    assert math.isclose(annualise(1.0, 1), 4095.0)


def test_annual_rate_is_unchanged():
    assert math.isclose(annualise(0.20, 12), 0.20)


def test_fails_on_ponzi_returns():
    assert fails(0.30, 1, T, bench=0.20)


def test_does_not_fail_near_tbill_rates():
    assert not fails(0.02, 1, T, bench=0.20)  # ~27% a year


def test_describe_mentions_yearly_figure():
    assert "2,230%" in describe(0.30, 1, bench=None)
