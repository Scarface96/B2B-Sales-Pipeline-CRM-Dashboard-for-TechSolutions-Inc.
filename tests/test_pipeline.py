import numpy as np
import pytest

from analysis import data


@pytest.fixture(scope="module")
def df():
    return data.clean(data.load())


def test_cleaning_fixes_known_issues(df):
    assert "GTXPro" not in set(df["product"])
    assert "technolgy" not in set(df["sector"])
    assert df["sales_price"].notna().all(), "every deal should match a product after cleaning"


def test_headline_numbers_match_the_excel_dashboard(df):
    won = df[df["won"] == 1]
    assert len(won) == 4238
    assert won["close_value"].sum() == pytest.approx(10_005_534)
    assert df.loc[df["closed"], "won"].mean() == pytest.approx(0.6315, abs=1e-4)


def test_wilson_interval_contains_the_rate_and_narrows_with_data():
    lo1, hi1 = data.wilson(np.array([6]), np.array([10]))
    lo2, hi2 = data.wilson(np.array([600]), np.array([1000]))
    assert lo1[0] < 0.6 < hi1[0]
    assert (hi2 - lo2)[0] < (hi1 - lo1)[0]


def test_agent_table_has_every_agent(df):
    t = data.agent_table(df)
    assert len(t) == df["sales_agent"].nunique()
    assert set(t["vs_team"]) <= {"Above", "Below", "In line"}


def test_open_pipeline_value_is_bounded_by_list_value(df):
    eng, s = data.open_pipeline(df)
    assert s["engaging_deals"] == 1589
    assert 0 < s["expected_value"] < s["list_value"] * 1.2
    assert eng["p_win"].between(0, 1).all()
    assert s["stale_deals"] <= s["engaging_deals"]
