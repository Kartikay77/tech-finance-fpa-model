import mysql.connector
import pandas as pd

# -----------------------------
# 1. CONNECT TO MYSQL
# -----------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="techfinance"
)

# -----------------------------
# 2. TEAM-LEVEL OPEX
# -----------------------------
team_opex_query = """
WITH hc AS (
    SELECT
        month,
        team_id,
        SUM(
            headcount
            * avg_salary
            / 12
            * (1 + bonus_pct / 100 + benefits_pct / 100)
        ) AS headcount_cost
    FROM headcount_costs
    GROUP BY month, team_id
),

cloud AS (
    SELECT
        month,
        team_id,
        SUM(actual_cost) AS cloud_cost
    FROM cloud_costs
    GROUP BY month, team_id
),

vendor AS (
    SELECT
        month,
        team_id,
        SUM(actual_cost) AS vendor_cost
    FROM vendor_costs
    GROUP BY month, team_id
)

SELECT
    hc.month,
    t.team_name,
    hc.headcount_cost,
    cloud.cloud_cost,
    vendor.vendor_cost,
    (
        hc.headcount_cost
        + cloud.cloud_cost
        + vendor.vendor_cost
    ) AS total_opex
FROM hc
JOIN cloud
    ON hc.month = cloud.month
    AND hc.team_id = cloud.team_id
JOIN vendor
    ON hc.month = vendor.month
    AND hc.team_id = vendor.team_id
JOIN teams t
    ON hc.team_id = t.team_id
ORDER BY hc.month, total_opex DESC;
"""

team_opex = pd.read_sql(team_opex_query, conn)

print("\nTEAM LEVEL OPEX")
print(team_opex.head(10))

# -----------------------------
# 3. ANNUAL TEAM OPEX
# -----------------------------
team_opex["month"] = pd.to_datetime(team_opex["month"])
team_opex["year"] = team_opex["month"].dt.year

annual_team_opex = (
    team_opex.groupby(["year", "team_name"])[
        ["headcount_cost", "cloud_cost", "vendor_cost", "total_opex"]
    ]
    .sum()
    .reset_index()
)

print("\nANNUAL TEAM OPEX")
print(annual_team_opex)

# -----------------------------
# 4. COST MIX
# -----------------------------
cost_mix = (
    annual_team_opex.groupby("year")[
        ["headcount_cost", "cloud_cost", "vendor_cost"]
    ]
    .sum()
    .reset_index()
)

cost_mix["total"] = (
    cost_mix["headcount_cost"]
    + cost_mix["cloud_cost"]
    + cost_mix["vendor_cost"]
)

cost_mix["headcount_pct"] = (
    cost_mix["headcount_cost"] / cost_mix["total"] * 100
)

cost_mix["cloud_pct"] = (
    cost_mix["cloud_cost"] / cost_mix["total"] * 100
)

cost_mix["vendor_pct"] = (
    cost_mix["vendor_cost"] / cost_mix["total"] * 100
)

print("\nANNUAL COST MIX")
print(cost_mix)

# -----------------------------
# 5. CLOUD BUDGET VARIANCE
# -----------------------------
variance_query = """
SELECT
    b.month,
    t.team_name,
    b.budget_amount,
    SUM(c.actual_cost) AS actual_amount,
    SUM(c.actual_cost) - b.budget_amount AS variance_amount,
    ((SUM(c.actual_cost) - b.budget_amount)
        / b.budget_amount) * 100 AS variance_pct
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
    b.budget_amount;
"""

variance = pd.read_sql(variance_query, conn)

top_over_budget = variance.sort_values(
    "variance_pct",
    ascending=False
).head(10)

print("\nTOP CLOUD BUDGET OVERRUNS")
print(top_over_budget)

# -----------------------------
# 6. FORECAST SCENARIO SUMMARY
# -----------------------------
forecast_query = """
SELECT
    month,
    scenario_name,
    SUM(forecast_amount) AS total_forecast
FROM forecast
GROUP BY month, scenario_name
ORDER BY month, scenario_name;
"""

forecast = pd.read_sql(forecast_query, conn)

forecast["month"] = pd.to_datetime(forecast["month"])
forecast["year"] = forecast["month"].dt.year

annual_forecast = (
    forecast.groupby(["year", "scenario_name"])["total_forecast"]
    .sum()
    .reset_index()
)

forecast_pivot = annual_forecast.pivot(
    index="year",
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

print("\nANNUAL FORECAST SCENARIO SUMMARY")
print(forecast_pivot)

# -----------------------------
# 7. 2025 VS 2026 OPEX GROWTH
# -----------------------------
yearly_opex = (
    annual_team_opex.groupby("year")["total_opex"]
    .sum()
    .reset_index()
)

if len(yearly_opex) >= 2:
    opex_2025 = yearly_opex.loc[
        yearly_opex["year"] == 2025,
        "total_opex"
    ].iloc[0]

    opex_2026 = yearly_opex.loc[
        yearly_opex["year"] == 2026,
        "total_opex"
    ].iloc[0]

    growth_pct = (
        (opex_2026 - opex_2025)
        / opex_2025
        * 100
    )

    print("\n2025 VS 2026 OPEX GROWTH")
    print(f"2025 OPEX: ${opex_2025:,.2f}")
    print(f"2026 OPEX: ${opex_2026:,.2f}")
    print(f"Growth: {growth_pct:.2f}%")

# -----------------------------
# 8. MANAGEMENT INSIGHTS
# -----------------------------
largest_team = (
    annual_team_opex[
        annual_team_opex["year"] == 2026
    ]
    .sort_values("total_opex", ascending=False)
    .iloc[0]
)

print("\nMANAGEMENT INSIGHTS")
print(
    f"Largest 2026 cost center: "
    f"{largest_team['team_name']} "
    f"(${largest_team['total_opex']:,.2f})"
)

latest_year = forecast_pivot[
    forecast_pivot["year"] == 2026
].iloc[0]

print(
    f"2026 savings opportunity vs Base: "
    f"${latest_year['Savings_vs_Base']:,.2f}"
)

print(
    f"2026 incremental High Growth spend: "
    f"${latest_year['High_Growth_Increment']:,.2f}"
)

# -----------------------------
# MONTHLY ACTUAL OPEX
# -----------------------------
monthly_actuals_query = """
WITH hc AS (
    SELECT
        month,
        SUM(
            headcount * avg_salary / 12
            * (1 + bonus_pct / 100 + benefits_pct / 100)
        ) AS headcount_cost
    FROM headcount_costs
    GROUP BY month
),

cloud AS (
    SELECT
        month,
        SUM(actual_cost) AS cloud_cost
    FROM cloud_costs
    GROUP BY month
),

vendor AS (
    SELECT
        month,
        SUM(actual_cost) AS vendor_cost
    FROM vendor_costs
    GROUP BY month
)

SELECT
    hc.month,
    hc.headcount_cost,
    cloud.cloud_cost,
    vendor.vendor_cost,
    (
        hc.headcount_cost
        + cloud.cloud_cost
        + vendor.vendor_cost
    ) AS total_actual_opex
FROM hc
JOIN cloud
    ON hc.month = cloud.month
JOIN vendor
    ON hc.month = vendor.month
ORDER BY hc.month;
"""

monthly_actuals = pd.read_sql(
    monthly_actuals_query,
    conn
)

monthly_actuals.to_csv(
    "monthly_actual_opex.csv",
    index=False
)

print("\nMONTHLY ACTUAL OPEX")
print(monthly_actuals)

print("\nmonthly_actual_opex.csv created.")

# -----------------------------
# 9. SAVE OUTPUTS
# -----------------------------
annual_team_opex.to_csv(
    "annual_team_opex.csv",
    index=False
)

cost_mix.to_csv(
    "annual_cost_mix.csv",
    index=False
)

top_over_budget.to_csv(
    "top_cloud_budget_overruns.csv",
    index=False
)

forecast_pivot.to_csv(
    "management_forecast_summary.csv",
    index=False
)

print("\nManagement summary files created successfully.")

conn.close()