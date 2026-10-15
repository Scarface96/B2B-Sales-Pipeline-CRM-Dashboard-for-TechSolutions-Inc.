"""Export model-ready tables for Tableau and Power BI.

    python -m bi.build_bi

Writes bi/data/*.csv (a small star schema) and bi/kpis.json (the headline numbers your
dashboard should show, so you can check a Tableau or Power BI build against this repo).
Uses the same cleaning as the live report (product and sector typos fixed), so every
figure matches it.
"""

import json
from pathlib import Path

import pandas as pd

from analysis import data as d

OUT = Path(__file__).resolve().parent


def tables(df: pd.DataFrame, raw: dict) -> dict:
    eng, _ = d.open_pipeline(df)
    fact = df[[
        "opportunity_id", "sales_agent", "product", "account", "deal_stage",
        "engage_date", "close_date", "close_value", "won", "closed", "open",
        "cycle_days", "age_days", "close_quarter", "price_realisation",
    ]].copy()
    fact["closed"] = fact["closed"].astype(int)
    fact["open"] = fact["open"].astype(int)
    # Weighted pipeline for Engaging deals (same model as the live report); blank for other stages.
    fact = fact.merge(eng[["opportunity_id", "p_win", "expected_value", "stale"]], on="opportunity_id", how="left")
    fact["stale"] = fact["stale"].astype("boolean").astype("Int64")

    dim_agent = raw["teams"].sort_values("sales_agent").reset_index(drop=True)
    dim_product = raw["products"].sort_values("product").reset_index(drop=True)
    acc = raw["accounts"].copy()
    acc["sector"] = acc["sector"].replace({"technolgy": "technology"})
    dim_account = acc.sort_values("account").reset_index(drop=True)
    return {"dim_agent": dim_agent, "dim_product": dim_product, "dim_account": dim_account, "fact_opportunity": fact}


def kpis(df: pd.DataFrame) -> dict:
    closed = df[df["closed"]]
    won = df[df["won"] == 1]
    _, s = d.open_pipeline(df)
    return {
        "Opportunities": int(len(df)),
        "Won deals": int(won.shape[0]),
        "Won revenue": round(float(won["close_value"].sum()), 0),
        "Win rate (closed deals)": round(float(closed["won"].mean()), 4),
        "Average won deal": round(float(won["close_value"].mean()), 2),
        "Median sales cycle (won, days)": float(won["cycle_days"].median()),
        "Engaging deals": int(s["engaging_deals"]),
        "Weighted pipeline (Engaging)": round(s["expected_value"], 0),
        "Stale Engaging deals": int(s["stale_deals"]),
        "Stale cutoff (days)": round(s["stale_cutoff_days"], 1),
    }


def build(out: Path = OUT) -> dict:
    raw = d.load()
    df = d.clean(raw)
    t = tables(df, raw)
    (out / "data").mkdir(parents=True, exist_ok=True)
    for name, frame in t.items():
        frame.to_csv(out / "data" / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    k = kpis(df)
    (out / "kpis.json").write_text(json.dumps(k, indent=2) + "\n")
    return {"tables": t, "kpis": k}


if __name__ == "__main__":
    res = build()
    for name, frame in res["tables"].items():
        print(f"{name}: {len(frame):,} rows")
    print(json.dumps(res["kpis"], indent=2))
