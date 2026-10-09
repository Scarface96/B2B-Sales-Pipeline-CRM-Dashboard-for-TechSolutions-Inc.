# 💼 B2B Sales Pipeline CRM Dashboard — TechSolutions Inc.

**Sales & CRM Analytics | Excel • PivotTables • Python • Statistics • Pipeline Forecasting • Interactive Reporting**

An Excel dashboard that tracks the B2B sales pipeline of a fictional computer hardware company, **TechSolutions Inc.**, showing quarterly sales performance by deal stage, sales agent, manager and region.

![Excel](https://img.shields.io/badge/Microsoft_Excel-217346?style=flat-square&logo=microsoft-excel&logoColor=white)
![Data Analysis](https://img.shields.io/badge/Data_Analysis-4285F4?style=flat-square)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)

## 🌐 Live Report

**[scarface96.github.io/B2B-Sales-Pipeline-CRM-Dashboard-for-TechSolutions-Inc.](https://scarface96.github.io/B2B-Sales-Pipeline-CRM-Dashboard-for-TechSolutions-Inc./)**

The Excel dashboard is still here. The same CSVs now also feed a Python analysis that publishes an interactive web report, rebuilt by GitHub Actions on every push.

**What the Python analysis adds:**

- **Data cleaning in code:** the `GTXPro` / `GTX Pro` mismatch and the `technolgy` sector typo are fixed before joining
- **Win rates with 95% confidence ranges:** 28 of 30 agents are within normal variation of the team's 63%, so ranking agents on win rate mostly rewards luck
- **What makes a top agent:** value won rises with deal volume (r = 0.81), not with a better win rate
- **Sales cycles:** lost deals die fast (median 14 days); deals still alive after two weeks win 69% of the time
- **Pipeline health:** 90% of wins close within 106 days, yet **1,432 of 1,589 Engaging deals are older than that**. The weighted pipeline looks worth $2.5M, but only about $0.25M sits in deals within a normal sales cycle
- **Weighted pipeline forecast:** list price × typical price realisation × each agent's product win rate (shrunk toward the product average)
- **Interactive leaderboard:** filter by manager or region, search agents, sort any column

## Business value

Consolidate CRM opportunities into quarterly views for sales managers. PivotTables, charts and slicers make deal stages, agent performance and regional differences easier to explore.

### Questions this project addresses

- How does the mix of won, lost and open opportunities vary by quarter?
- Which agents and regions contribute the most won deal value?
- How does performance change when filtering by manager?


## 📋 Overview

Sales managers need to see at a glance how their teams are doing each quarter. This project takes raw CRM data — 8,800 sales opportunities handled by 35 sales agents — and turns it into an interactive dashboard for tracking quarter-by-quarter performance.

## 📈 Results at a Glance

Charts built with Python (pandas + matplotlib) from the data files in this repo.

<p align="center"><img src="docs/images/quarterly_won.png" alt="Won deal value by quarter" width="85%"></p>

<p align="center"><img src="docs/images/top_agents.png" alt="Top 8 sales agents by won deal value" width="85%"></p>

## 🗂️ Dataset

| File | Rows | Description |
|------|------|-------------|
| `sales_pipeline.csv` | 8,800 | Every opportunity: agent, product, account, deal stage, engage/close dates, close value |
| `sales_teams.csv` | 35 | Sales agents, their managers and regional office |
| `accounts.csv` | 85 | Customer companies: sector, year established, revenue, employees, location |
| `products.csv` | 7 | Product catalogue with series and list price |
| `data_dictionary.csv` | 21 | Field definitions for every table |

**Deal stages:** Prospecting → Engaging → Won / Lost
**Period:** deals closed March – December 2017

## 📊 Dashboard

`CRM SALES DASHBOARD.xlsx` contains:

- **sales_pipeline** and **sales_teams** — the source data, with each agent's manager and regional office joined onto the pipeline
- **Quarterly Sales Performance** — the dashboard:
  - PivotTables counting opportunities per quarter, broken down by **deal stage** and by **sales agent**
  - A **pie chart** and a **bar chart** summarising the pipeline
  - **Slicers** for **manager** and **regional office** to filter the whole view

## 💡 Key Figures (from the data)

- **4,238 deals won**, worth about **$10.0M** in total
- **Win rate of 63%** on closed deals (won vs. lost)
- **West** was the top region (~$3.6M), ahead of Central (~$3.3M) and East (~$3.1M)
- **GTX Pro** was the top revenue product (~$3.5M)
- **Darcel Schlecht** was the top-performing agent (~$1.15M closed)

> Data-quality note: the product `GTX Pro` appears as `GTXPro` in the pipeline table but `GTX Pro` in the product table, so the two need standardising before joining.

## 📁 Repository Contents

```
├── analysis/
│   ├── data.py        # Load, clean, join; win rates with Wilson intervals; agent table; open-pipeline value
│   ├── report.py      # Turns the analysis into the interactive web page
│   └── build.py       # Charts, leaderboard and site/index.html
├── tests/             # pytest checks (cleaning, headline totals, intervals, pipeline bounds)
├── .github/workflows/deploy.yml   # Test, build and publish to GitHub Pages
├── CRM SALES DASHBOARD.xlsx   # Excel dashboard
├── sales_pipeline.csv, sales_teams.csv, accounts.csv, products.csv, data_dictionary.csv
└── requirements.txt
```

**Run the Python report locally:**

```bash
pip install -r requirements.txt
python -m pytest
python -m analysis.build    # writes site/index.html
```

## 🚀 How to Use

Download `CRM SALES DASHBOARD.xlsx`, open it in Microsoft Excel, and use the slicers on the **Quarterly Sales Performance** sheet to filter by manager or regional office.

## 🛠️ Skills Demonstrated

Data preparation · PivotTables & PivotCharts · date grouping by quarter · slicers & interactive filtering · dashboard layout · sales pipeline analysis

---

👤 **Tony Mulunda** — [GitHub @Scarface96](https://github.com/Scarface96)

## Interpretation & limitations

TechSolutions Inc. is fictional. Closed-deal win rate excludes open opportunities. Won deal value is a historical sales measure; the workbook should not be presented as a validated revenue forecast.

## Explore the analytics portfolio

- [sql_retail_sales_p1](https://github.com/Scarface96/sql_retail_sales_p1)
- [HR-Analysis-Dashboard](https://github.com/Scarface96/HR-Analysis-Dashboard)
- [Global-CO2-Emissions-Dashboard](https://github.com/Scarface96/Global-CO2-Emissions-Dashboard)
- [Toy-Store-KPI-Report](https://github.com/Scarface96/Toy-Store-KPI-Report)

## About This Project

A business intelligence project designed to help sales leaders understand pipeline health, team performance and regional results. It demonstrates Excel-based CRM analytics, PivotTables, interactive filtering and the ability to translate sales data into management-ready insights.
