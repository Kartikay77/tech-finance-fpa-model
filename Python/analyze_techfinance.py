import mysql.connector
import pandas as pd

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="techfinance"
)

# -----------------------------
# 1. CLOUD BUDGET VS ACTUAL
# -----------------------------
cloud_variance_query = """
SELECT
    b.month,
    t.team_name,
    b.budget_amount,
    SUM(c.actual_cost) AS actual_amount,
    SUM(c.actual_cost) - b.budget_amount AS variance_amount,
    ((SUM(c.actual_cost) - b.budget_amount) / b.budget_amount) * 100 AS variance_pct
FROM budget b
JOIN teams t
    ON b.team_id = t.team_id
JOIN cloud_costs c
    ON b.team_id = c.team_id
    AND b.month = c.month
WHERE b.cost_category = 'Cloud'
GROUP BY
    b.month,
    t.team_name,
    b.budget_amount
ORDER BY
    b.month,
    variance_pct DESC;
"""

cloud_variance = pd.read_sql(cloud_variance_query, conn)

print("\nCLOUD BUDGET VS ACTUAL")
print(cloud_variance.head(10))


# -----------------------------
# 2. HEADCOUNT COST
# -----------------------------
headcount_query = """
SELECT
    h.month,
    t.team_name,
    SUM(
        h.headcount
        * h.avg_salary
        / 12
        * (1 + h.bonus_pct / 100 + h.benefits_pct / 100)
    ) AS monthly_headcount_cost
FROM headcount_costs h
JOIN teams t
    ON h.team_id = t.team_id
GROUP BY
    h.month,
    t.team_name
ORDER BY
    h.month,
    monthly_headcount_cost DESC;
"""

headcount = pd.read_sql(headcount_query, conn)

print("\nHEADCOUNT COST")
print(headcount.head(10))


# -----------------------------
# 3. FORECAST SCENARIOS
# -----------------------------
forecast_query = """
SELECT
    month,
    scenario_name,
    SUM(forecast_amount) AS total_forecast
FROM forecast
GROUP BY
    month,
    scenario_name
ORDER BY
    month,
    scenario_name;
"""

forecast = pd.read_sql(forecast_query, conn)

print("\nFORECAST SCENARIOS")
print(forecast.head(10))


# -----------------------------
# 4. SCENARIO PIVOT
# -----------------------------
forecast_pivot = forecast.pivot(
    index="month",
    columns="scenario_name",
    values="total_forecast"
).reset_index()

forecast_pivot["Savings_vs_Base"] = (
    forecast_pivot["Base"]
    - forecast_pivot["Cost Reduction"]
)

forecast_pivot["High_Growth_Increment"] = (
    forecast_pivot["High Growth"]
    - forecast_pivot["Base"]
)

forecast_pivot["Savings_pct"] = (
    forecast_pivot["Savings_vs_Base"]
    / forecast_pivot["Base"]
    * 100
)

print("\nSCENARIO COMPARISON")
print(forecast_pivot.tail(12))


# -----------------------------
# 5. ANNUAL SUMMARY
# -----------------------------
forecast_pivot["year"] = pd.to_datetime(
    forecast_pivot["month"]
).dt.year

annual_summary = forecast_pivot.groupby("year").agg({
    "Base": "sum",
    "High Growth": "sum",
    "Cost Reduction": "sum",
    "Savings_vs_Base": "sum",
    "High_Growth_Increment": "sum"
}).reset_index()

print("\nANNUAL FORECAST SUMMARY")
print(annual_summary)


# -----------------------------
# 6. SAVE OUTPUTS
# -----------------------------
cloud_variance.to_csv(
    "cloud_budget_variance.csv",
    index=False
)

headcount.to_csv(
    "headcount_costs_summary.csv",
    index=False
)

forecast_pivot.to_csv(
    "forecast_scenario_analysis.csv",
    index=False
)

annual_summary.to_csv(
    "annual_forecast_summary.csv",
    index=False
)

print("\nCSV files created successfully.")

conn.close()