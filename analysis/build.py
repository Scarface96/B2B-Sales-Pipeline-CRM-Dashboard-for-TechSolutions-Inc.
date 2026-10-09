"""Run the CRM pipeline analysis and write the website to site/index.html.

    python -m analysis.build
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import data
from .report import AXIS, BLUE, GRID, INK_2, MUTED, ORANGE, Report, money, style, table_html, to_json

REPO = "Scarface96/B2B-Sales-Pipeline-CRM-Dashboard-for-TechSolutions-Inc."
GREY = "#b9b8b1"


def quarter_figure(q: pd.DataFrame) -> go.Figure:
    fig = make_subplots(rows=1, cols=2, subplot_titles=["Won deal value", "Win rate on closed deals"], horizontal_spacing=0.1)
    fig.add_bar(x=q["close_quarter"], y=q["won_value"], marker_color=BLUE, showlegend=False,
                customdata=q["won"], hovertemplate="%{x}<br>%{y:$,.0f} from %{customdata:,} deals<extra></extra>", row=1, col=1)
    fig.add_scatter(x=q["close_quarter"], y=q["win_rate"], mode="lines+markers", line=dict(color=BLUE, width=2),
                    marker=dict(size=9, line=dict(color="#fcfcfb", width=2)), showlegend=False,
                    hovertemplate="%{x}<br>Win rate %{y:.0%}<extra></extra>", row=1, col=2)
    style(fig, height=340)
    fig.update_annotations(font=dict(size=14, color=INK_2))
    fig.update_yaxes(tickprefix="$", row=1, col=1)
    fig.update_yaxes(tickformat=".0%", range=[0.5, 0.9], row=1, col=2)
    return fig


def agent_ci_figure(agents: pd.DataFrame, team_rate: float) -> go.Figure:
    t = agents.sort_values("win_rate")
    color = {"Above": BLUE, "Below": ORANGE, "In line": GREY}
    fig = go.Figure()
    for status in ["In line", "Above", "Below"]:
        g = t[t["vs_team"] == status]
        if g.empty:
            continue
        fig.add_scatter(
            x=g["win_rate"], y=g["sales_agent"], mode="markers", name={"In line": "Within normal variation", "Above": "Clearly above the team", "Below": "Clearly below the team"}[status],
            marker=dict(color=color[status], size=10, line=dict(color="#fcfcfb", width=2)),
            error_x=dict(type="data", symmetric=False, array=g["ci_high"] - g["win_rate"], arrayminus=g["win_rate"] - g["ci_low"], color=color[status], thickness=1.5, width=0),
            customdata=np.stack([g["won"], g["closed"], g["ci_low"], g["ci_high"]], axis=1),
            hovertemplate="%{y}<br>Win rate %{x:.0%} (%{customdata[0]} of %{customdata[1]})<br>95% range %{customdata[2]:.0%}–%{customdata[3]:.0%}<extra></extra>",
        )
    fig.add_vline(x=team_rate, line=dict(color=MUTED, dash="dot", width=1), annotation_text=f"Team {team_rate:.0%}", annotation_position="top", annotation_font_color=MUTED)
    style(fig, height=760)
    fig.update_xaxes(tickformat=".0%", showgrid=True, gridcolor=GRID, title="Win rate on closed deals, with 95% confidence range")
    fig.update_yaxes(showgrid=False, tickfont=dict(size=12))
    return fig


def volume_figure(agents: pd.DataFrame) -> go.Figure:
    r = np.corrcoef(agents["closed"], agents["won_value"])[0, 1]
    fig = go.Figure(go.Scatter(
        x=agents["closed"], y=agents["won_value"], mode="markers",
        marker=dict(color=BLUE, size=11, line=dict(color="#fcfcfb", width=2)),
        customdata=np.stack([agents["sales_agent"], agents["win_rate"], agents["avg_deal"]], axis=1),
        hovertemplate="%{customdata[0]}<br>%{x} deals closed, win rate %{customdata[1]:.0%}<br>Won %{y:$,.0f}, average deal %{customdata[2]:$,.0f}<extra></extra>",
    ))
    style(fig, height=400, legend=False)
    fig.update_xaxes(title="Deals closed (won + lost)", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title="Value won", tickprefix="$")
    fig.add_annotation(x=0.02, y=0.96, xref="paper", yref="paper", text=f"Correlation r = {r:.2f}", showarrow=False, xanchor="left", font=dict(color=MUTED, size=13))
    return fig


def cycle_figure(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    bins = dict(start=0, end=140, size=7)
    for stage, color in [("Won", BLUE), ("Lost", ORANGE)]:
        g = df[df["deal_stage"] == stage]
        fig.add_histogram(x=g["cycle_days"], name=f"{stage} (median {g['cycle_days'].median():.0f} days)", xbins=bins, marker_color=color, opacity=0.85,
                          hovertemplate=f"{stage}: %{{y}} deals closed in %{{x}} days<extra></extra>")
    style(fig, height=380)
    fig.update_layout(barmode="group", bargap=0.1)
    fig.update_xaxes(title="Days from engagement to close")
    fig.update_yaxes(title="Deals")
    return fig


def age_figure(eng: pd.DataFrame, won_cycles: pd.Series, cutoff: float) -> go.Figure:
    fig = go.Figure()
    bins = dict(start=0, end=440, size=10)
    fig.add_histogram(x=won_cycles, name="Won deals: days to close", xbins=bins, marker_color=BLUE, opacity=0.85,
                      hovertemplate="%{y} won deals closed after %{x} days<extra></extra>")
    fig.add_histogram(x=eng["age_days"], name="Open deals: days since engagement", xbins=bins, marker_color=ORANGE, opacity=0.85,
                      hovertemplate="%{y} open deals have been open %{x} days<extra></extra>")
    fig.add_vline(x=cutoff, line=dict(color=INK_2, dash="dot", width=1.5), annotation_text=f"90% of wins close within {cutoff:.0f} days", annotation_position="top right", annotation_font_color=INK_2)
    style(fig, height=400)
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title="Days")
    fig.update_yaxes(title="Deals")
    return fig


def product_figure(prod: pd.DataFrame) -> go.Figure:
    t = prod.sort_values("won_value")
    fig = go.Figure(go.Bar(
        x=t["won_value"], y=t["product"], orientation="h", marker_color=BLUE,
        customdata=np.stack([t["won"], t["win_rate"], t["realisation"]], axis=1),
        hovertemplate="%{y}<br>Won %{x:$,.0f} from %{customdata[0]} deals<br>Win rate %{customdata[1]:.0%}, closes at %{customdata[2]:.0%} of list price<extra></extra>",
    ))
    style(fig, height=340, legend=False)
    fig.update_xaxes(tickprefix="$", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(showgrid=False)
    return fig


LEADERBOARD = """
<form class="controls" id="lb-filters" onsubmit="return false">
  <label>Manager<select id="lb-manager"><option value="">All managers</option></select></label>
  <label>Region<select id="lb-region"><option value="">All regions</option></select></label>
  <label>Find an agent<input id="lb-search" type="search" placeholder="Type a name"></label>
</form>
<div class="readout" aria-live="polite">
  <div><b id="lb-agents">–</b><span>agents shown</span></div>
  <div><b id="lb-value">–</b><span>value won</span></div>
  <div><b id="lb-rate">–</b><span>win rate</span></div>
  <div><b id="lb-open">–</b><span>open deals</span></div>
</div>
<div class="table-wrap" style="margin-top:14px;max-height:520px;overflow:auto"><table id="lb">
<thead><tr>
<th data-k="sales_agent">Agent</th><th data-k="manager">Manager</th><th data-k="regional_office">Region</th>
<th data-k="won_value" class="num">Value won</th><th data-k="won" class="num">Deals won</th><th data-k="win_rate" class="num">Win rate</th>
<th data-k="avg_deal" class="num">Avg deal</th><th data-k="cycle_days" class="num">Median days to win</th><th data-k="open_deals" class="num">Open deals</th><th data-k="vs_team">vs team</th>
</tr></thead><tbody></tbody></table></div>
<p class="note">Click a column heading to sort. "vs team" uses the 95% confidence range, so it only says Above or Below when the difference is unlikely to be chance.</p>
"""


def leaderboard_js(agents: pd.DataFrame) -> str:
    rows = agents[["sales_agent", "manager", "regional_office", "won_value", "won", "closed", "win_rate", "avg_deal", "cycle_days", "open_deals", "vs_team"]].round(4).to_dict("records")
    return f"""
(function(){{
const R={to_json(rows)};
const $=id=>document.getElementById(id);
let key='won_value', dir=-1;
const uniq=k=>[...new Set(R.map(r=>r[k]))].sort();
uniq('manager').forEach(m=>$('lb-manager').add(new Option(m,m)));
uniq('regional_office').forEach(m=>$('lb-region').add(new Option(m,m)));
const money=v=>'$'+Math.round(v).toLocaleString();
function render(){{
  const m=$('lb-manager').value, g=$('lb-region').value, q=$('lb-search').value.trim().toLowerCase();
  const rows=R.filter(r=>(!m||r.manager===m)&&(!g||r.regional_office===g)&&(!q||r.sales_agent.toLowerCase().includes(q)))
    .sort((a,b)=>(a[key]>b[key]?1:a[key]<b[key]?-1:0)*dir);
  $('lb').tBodies[0].innerHTML=rows.map(r=>`<tr><td>${{r.sales_agent}}</td><td>${{r.manager}}</td><td>${{r.regional_office}}</td>
    <td class="num">${{money(r.won_value)}}</td><td class="num">${{r.won}}</td><td class="num">${{(r.win_rate*100).toFixed(1)}}%</td>
    <td class="num">${{money(r.avg_deal)}}</td><td class="num">${{r.cycle_days}}</td><td class="num">${{r.open_deals}}</td><td>${{r.vs_team}}</td></tr>`).join('');
  const won=rows.reduce((s,r)=>s+r.won,0), closed=rows.reduce((s,r)=>s+r.closed,0);
  $('lb-agents').textContent=rows.length;
  $('lb-value').textContent=money(rows.reduce((s,r)=>s+r.won_value,0));
  $('lb-rate').textContent=closed?(won/closed*100).toFixed(1)+'%':'–';
  $('lb-open').textContent=rows.reduce((s,r)=>s+r.open_deals,0).toLocaleString();
  document.querySelectorAll('#lb th').forEach(th=>{{th.setAttribute('aria-sort',th.dataset.k===key?(dir>0?'ascending':'descending'):'none'); th.style.cursor='pointer'; th.style.textDecoration=th.dataset.k===key?'underline':'none';}});
}}
document.querySelectorAll('#lb th').forEach(th=>th.addEventListener('click',()=>{{dir=th.dataset.k===key?-dir:(typeof R[0][th.dataset.k]==='string'?1:-1); key=th.dataset.k; render();}}));
['lb-manager','lb-region','lb-search'].forEach(id=>$(id).addEventListener('input',render));
render();
}})();
"""


def main(out="site/index.html"):
    df = data.clean(data.load())
    closed = df[df["closed"]]
    team_rate = closed["won"].mean()
    won = df[df["won"] == 1]
    agents = data.agent_table(df)
    q = data.quarterly(df)
    eng, pipe = data.open_pipeline(df)
    prod = data.win_rates(df, "product").merge(
        won.groupby("product").agg(realisation=("price_realisation", "median"), avg_deal=("close_value", "mean")), on="product")
    region = data.win_rates(df, "regional_office")
    top = agents.iloc[0]
    stale_share = pipe["stale_deals"] / pipe["engaging_deals"]
    fresh_ev = pipe["expected_value"] - pipe["stale_expected_value"]
    r_vol = np.corrcoef(agents["closed"], agents["won_value"])[0, 1]
    n_above, n_below = int((agents["vs_team"] == "Above").sum()), int((agents["vs_team"] == "Below").sum())
    med_won, med_lost = won["cycle_days"].median(), df.loc[df["deal_stage"] == "Lost", "cycle_days"].median()
    late_rate = closed.loc[closed["cycle_days"] > 14, "won"].mean()

    r = Report(
        title=f"{stale_share:.0%} of open deals are older than almost any deal TechSolutions has ever won",
        project="B2B Sales Pipeline: TechSolutions Inc.",
        summary=(
            f"In 2017 the sales team won {len(won):,} deals worth {money(won['close_value'].sum())}, closing {team_rate:.0%} of the deals it finished. "
            "Win rates are remarkably even across regions, managers and products. The real risk sits in the open pipeline: most "
            "deals marked as in progress have been open far longer than winning deals ever take."
        ),
        repo=REPO,
        accent=BLUE,
        source="sales_pipeline.csv (8,800 opportunities), sales_teams.csv (35 agents), accounts.csv (85 companies) and products.csv (7 products), for a fictional hardware company.",
        method=(
            "pandas cleans and joins the four tables (fixing the GTXPro/GTX Pro mismatch and a sector typo). Win rates carry 95% Wilson "
            "confidence ranges. Open-deal value = list price × typical price realisation × win probability, where each agent's product "
            "win rate is shrunk toward the product average. A deal is stale once it has been open longer than 90% of won deals took to close."
        ),
    )
    r.kpis([
        (money(won["close_value"].sum()), "won in 2017", f"{len(won):,} deals"),
        (f"{team_rate:.0%}", "win rate", "on closed deals"),
        (f"{pipe['engaging_deals']:,}", "deals still engaging", f"{money(pipe['list_value'])} at list price"),
        (f"{stale_share:.0%}", "of those are stale", f"open over {pipe['stale_cutoff_days']:.0f} days"),
    ])

    r.section(
        "How did the year go?",
        f"<p>Won value held steady at about $3M a quarter from Q2. Q1 looks unusually good ({q.loc[0, 'win_rate']:.0%} win rate), "
        "but that's an artefact of where the data starts: only deals opened in late 2016 could close that early, and quick wins dominate. "
        f"From Q2 onward the win rate settles near {q.loc[1:, 'won'].sum() / (q.loc[1:, 'won'].sum() + q.loc[1:, 'lost'].sum()):.0%}.</p>",
        fig=quarter_figure(q),
        table=q.assign(win_rate=(q["win_rate"] * 100).round(1)).rename(columns={"close_quarter": "quarter", "won_value": "won value", "win_rate": "win rate %"}),
    )
    r.section(
        "Do some agents close better than others?",
        f"<p>Barely. Every agent's win rate is shown with its 95% confidence range. <b>{len(agents) - n_above - n_below} of {len(agents)} agents "
        f"are within normal variation of the team's {team_rate:.0%}</b>; only {n_above} sits clearly above and {n_below} clearly below. "
        "Ranking agents by win rate alone would mostly reward luck.</p>",
        fig=agent_ci_figure(agents, team_rate),
    )
    r.section(
        "So what makes a top agent?",
        f"<p>Volume. Value won rises closely with the number of deals an agent works (r = {r_vol:.2f}). "
        f"<b>{top['sales_agent']}</b> leads with {money(top['won_value'])}, not through a higher win rate ({top['win_rate']:.0%}) but by "
        f"closing {top['closed']} deals and selling bigger products (average {money(top['avg_deal'])}).</p>",
        fig=volume_figure(agents),
    )
    r.section(
        "How long do deals take?",
        f"<p>Lost deals usually die quickly: half are lost within <b>{med_lost:.0f} days</b>. Won deals take longer, a median of "
        f"<b>{med_won:.0f} days</b>, and none took longer than {won['cycle_days'].max():.0f}. That makes the first two weeks telling: "
        f"deals still alive after 14 days go on to win <b>{late_rate:.0%}</b> of the time, against {team_rate:.0%} overall.</p>",
        fig=cycle_figure(df),
    )
    r.section(
        "How healthy is the open pipeline?",
        f"<p>Not very. Ninety percent of won deals closed within <b>{pipe['stale_cutoff_days']:.0f} days</b>, yet <b>{pipe['stale_deals']:,} of the "
        f"{pipe['engaging_deals']:,} deals still marked Engaging</b> have been open longer than that, many for over a year. Weighted by "
        f"each agent's win rate, the Engaging pipeline looks worth <b>{money(pipe['expected_value'])}</b>; counting only deals still "
        f"within a normal sales cycle, it's closer to <b>{money(fresh_ev)}</b>.</p>"
        "<p>Either those deals are dead and should be closed out, or the CRM isn't being updated. Both are worth fixing before anyone forecasts from this pipeline. "
        f"A further {pipe['prospecting_deals']} deals are still in Prospecting ({money(pipe['prospecting_list_value'])} at list price), with no history to estimate how many will progress.</p>",
        fig=age_figure(eng, won["cycle_days"], pipe["stale_cutoff_days"]),
    )
    prod_t = prod[["product", "won", "won_value", "win_rate", "avg_deal", "realisation"]].copy()
    prod_t["win_rate"] = (prod_t["win_rate"] * 100).round(1)
    prod_t["realisation"] = (prod_t["realisation"] * 100).round(1)
    r.section(
        "Which products bring in the money?",
        f"<p><b>GTX Pro</b> and <b>GTX Plus Pro</b> bring in {prod.set_index('product').loc[['GTX Pro', 'GTX Plus Pro'], 'won_value'].sum() / prod['won_value'].sum():.0%} of won value. Win rates barely differ by product "
        f"({prod['win_rate'].min():.0%}–{prod['win_rate'].max():.0%}), and deals close at a median of "
        f"{won['price_realisation'].median():.0%} of list price, so there's no sign of systematic discounting.</p>",
        fig=product_figure(prod),
        table=prod_t.round(0).rename(columns={"won_value": "value won", "win_rate": "win rate %", "avg_deal": "avg deal", "realisation": "median % of list price"}),
    )
    region_t = region.assign(win_rate=(region["win_rate"] * 100).round(1), ci_low=(region["ci_low"] * 100).round(1), ci_high=(region["ci_high"] * 100).round(1))
    r.section(
        "Team leaderboard",
        "<p>Filter by manager or region to see each team's numbers, or search for an agent. "
        f"Regions are close: {', '.join(f'{x.regional_office} {x.win_rate:.0%}' for x in region.itertuples())}.</p>",
        html=LEADERBOARD + "<details><summary>Show the regional numbers</summary>" + table_html(region_t.rename(columns={"regional_office": "region", "won_value": "value won", "win_rate": "win rate %", "ci_low": "95% low", "ci_high": "95% high"})) + "</details>",
    )
    r.script(leaderboard_js(agents))

    path = r.write(out)
    print(f"Wrote {path} ({path.stat().st_size / 1024:.0f} KB). Stale open deals: {pipe['stale_deals']} of {pipe['engaging_deals']}.")
    return r


if __name__ == "__main__":
    main()
