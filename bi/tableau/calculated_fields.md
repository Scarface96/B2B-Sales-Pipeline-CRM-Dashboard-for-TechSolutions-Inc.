# Tableau calculated fields: B2B Sales Pipeline CRM Dashboard

Create each one with **Analysis → Create Calculated Field**, name it exactly as shown, and paste the formula.
Tableau shows CSV columns in title case (`new_cases` becomes *New Cases*). If yours show the raw names, use those in the formulas.

## Connect the data

Connect to the fact table, then drag each dimension table onto the canvas and relate it:

- `fact_opportunity.sales_agent` = `dim_agent.sales_agent`
- `fact_opportunity.product` = `dim_product.product`
- `fact_opportunity.account` = `dim_account.account`

## Fields

### Win Rate

```
SUM([Won]) / SUM([Closed])
```

### Won Revenue

```
SUM(IF [Won] = 1 THEN [Close Value] END)
```

### Team Win Rate

```
{ FIXED : SUM([Won]) } / { FIXED : SUM([Closed]) }
```

Use as a reference line on the agent win-rate bar.

### Pipeline Health

```
IF [Deal Stage] = "Engaging" THEN
    IF [Stale] = 1 THEN "Stale (older than 90% of wins)" ELSE "Within normal cycle" END
END
```

Colour for the pipeline-health bar.

### Weighted Pipeline

```
SUM([Expected Value])
```
