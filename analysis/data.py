"""Load, clean and join the CRM tables."""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AS_OF = pd.Timestamp("2017-12-31")  # last date in the data; open deals are measured to here


def load() -> dict[str, pd.DataFrame]:
    pipe = pd.read_csv(ROOT / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    teams = pd.read_csv(ROOT / "sales_teams.csv")
    accounts = pd.read_csv(ROOT / "accounts.csv")
    products = pd.read_csv(ROOT / "products.csv")
    return {"pipeline": pipe, "teams": teams, "accounts": accounts, "products": products}


def clean(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per opportunity with team, product and account details joined on."""
    pipe = t["pipeline"].copy()
    # Known data-quality issues
    pipe["product"] = pipe["product"].replace({"GTXPro": "GTX Pro"})
    accounts = t["accounts"].copy()
    accounts["sector"] = accounts["sector"].replace({"technolgy": "technology"})

    unknown = set(pipe["product"]) - set(t["products"]["product"])
    assert not unknown, f"unknown products after cleaning: {unknown}"

    df = (
        pipe.merge(t["teams"], on="sales_agent", how="left", validate="many_to_one")
        .merge(t["products"], on="product", how="left", validate="many_to_one")
        .merge(accounts[["account", "sector", "office_location"]], on="account", how="left", validate="many_to_one")
    )
    assert df["manager"].notna().all(), "every agent should have a manager"
    df["won"] = (df["deal_stage"] == "Won").astype(int)
    df["closed"] = df["deal_stage"].isin(["Won", "Lost"])
    df["open"] = df["deal_stage"].isin(["Engaging", "Prospecting"])
    df["cycle_days"] = (df["close_date"] - df["engage_date"]).dt.days
    df["age_days"] = np.where(df["deal_stage"] == "Engaging", (AS_OF - df["engage_date"]).dt.days, np.nan)
    df["close_quarter"] = df["close_date"].dt.to_period("Q").astype(str).str.replace("Q", " Q", regex=False)
    df["price_realisation"] = np.where(df["won"] == 1, df["close_value"] / df["sales_price"], np.nan)
    df["sector"] = df["sector"].fillna("unknown account")
    return df


def wilson(successes, trials, z: float = 1.96):
    """95% Wilson score interval for a proportion (works well for small samples)."""
    successes = np.asarray(successes, dtype=float)
    trials = np.asarray(trials, dtype=float)
    p = successes / trials
    denom = 1 + z**2 / trials
    centre = (p + z**2 / (2 * trials)) / denom
    half = z * np.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denom
    return centre - half, centre + half


def win_rates(df: pd.DataFrame, by) -> pd.DataFrame:
    closed = df[df["closed"]]
    g = closed.groupby(by).agg(closed=("won", "size"), won=("won", "sum"), won_value=("close_value", "sum")).reset_index()
    g["win_rate"] = g["won"] / g["closed"]
    g["ci_low"], g["ci_high"] = wilson(g["won"], g["closed"])
    return g


def agent_table(df: pd.DataFrame) -> pd.DataFrame:
    """Everything a sales manager wants per agent."""
    w = win_rates(df, ["sales_agent", "manager", "regional_office"])
    won = df[df["won"] == 1].groupby("sales_agent").agg(avg_deal=("close_value", "mean"), cycle_days=("cycle_days", "median"))
    open_ = df[df["open"]].groupby("sales_agent").agg(open_deals=("opportunity_id", "size"))
    t = w.merge(won, on="sales_agent", how="left").merge(open_, on="sales_agent", how="left")
    t["open_deals"] = t["open_deals"].fillna(0).astype(int)
    team_rate = df.loc[df["closed"], "won"].mean()
    t["vs_team"] = np.select([t["ci_low"] > team_rate, t["ci_high"] < team_rate], ["Above", "Below"], "In line")
    return t.sort_values("won_value", ascending=False).reset_index(drop=True)


def quarterly(df: pd.DataFrame) -> pd.DataFrame:
    closed = df[df["closed"]]
    q = closed.groupby("close_quarter").agg(won=("won", "sum"), lost=("won", lambda s: int((s == 0).sum())), won_value=("close_value", "sum")).reset_index()
    q["win_rate"] = q["won"] / (q["won"] + q["lost"])
    return q


def stale_cutoff(df: pd.DataFrame, pct: float = 0.9) -> float:
    """A deal open longer than 90% of won deals took to close is considered stale."""
    return float(df.loc[df["won"] == 1, "cycle_days"].quantile(pct))


def open_pipeline(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Expected value of deals in the Engaging stage.

    expected value = list price x typical price realisation (by product) x win probability
    The win probability is the agent's win rate on that product, shrunk toward the
    product's overall rate so small samples don't produce extreme guesses.
    """
    closed = df[df["closed"]]
    prod = closed.groupby("product")["won"].agg(["sum", "size"]).rename(columns={"sum": "w", "size": "n"})
    prod["rate"] = prod["w"] / prod["n"]
    pair = closed.groupby(["sales_agent", "product"])["won"].agg(["sum", "size"]).rename(columns={"sum": "w", "size": "n"}).reset_index()
    k = 20  # prior strength: like adding 20 deals at the product's average rate
    pair = pair.merge(prod["rate"], left_on="product", right_index=True)
    pair["p_win"] = (pair["w"] + k * pair["rate"]) / (pair["n"] + k)
    realisation = df[df["won"] == 1].groupby("product")["price_realisation"].median()

    eng = df[df["deal_stage"] == "Engaging"].merge(pair[["sales_agent", "product", "p_win"]], on=["sales_agent", "product"], how="left")
    eng["p_win"] = eng["p_win"].fillna(eng["product"].map(prod["rate"]))
    eng["expected_close"] = eng["sales_price"] * eng["product"].map(realisation)
    eng["expected_value"] = eng["expected_close"] * eng["p_win"]
    cutoff = stale_cutoff(df)
    eng["stale"] = eng["age_days"] > cutoff
    prospecting = df[df["deal_stage"] == "Prospecting"]
    summary = {
        "engaging_deals": len(eng),
        "list_value": float(eng["sales_price"].sum()),
        "expected_value": float(eng["expected_value"].sum()),
        "stale_deals": int(eng["stale"].sum()),
        "stale_expected_value": float(eng.loc[eng["stale"], "expected_value"].sum()),
        "stale_cutoff_days": cutoff,
        "prospecting_deals": len(prospecting),
        "prospecting_list_value": float(prospecting["sales_price"].sum()),
    }
    return eng, summary
