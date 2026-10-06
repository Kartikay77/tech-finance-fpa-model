import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime

np.random.seed(42)

# -----------------------------
# 1. CONNECT TO MYSQL
# -----------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="techfinance"
)

cursor = conn.cursor()

print("Connected to MySQL.")

# -----------------------------
# 2. CLEAR OLD TEST DATA
# -----------------------------
tables_to_clear = [
    "forecast",
    "budget",
    "vendor_costs",
    "cloud_costs",
    "headcount_costs"
]

for table in tables_to_clear:
    cursor.execute(f"DELETE FROM {table};")

conn.commit()

print("Old test data cleared.")

# -----------------------------
# 3. LOAD TEAMS
# -----------------------------
cursor.execute("""
SELECT team_id, team_name
FROM teams
ORDER BY team_id;
""")

teams = cursor.fetchall()

print("Teams:")
for team in teams:
    print(team)

# -----------------------------
# 4. DATE RANGE
# -----------------------------
months = pd.date_range(
    start="2025-01-01",
    end="2026-12-01",
    freq="MS"
)

# -----------------------------
# 5. TEAM CONFIGURATION
# -----------------------------
team_config = {
    1: {
        "roles": {
            "Software Engineer": (42, 190000),
            "Engineering Manager": (5, 240000),
            "Product Manager": (4, 210000)
        },
        "cloud_multiplier": 1.0
    },

    2: {
        "roles": {
            "Software Engineer": (55, 195000),
            "Engineering Manager": (6, 245000),
            "Product Manager": (5, 215000)
        },
        "cloud_multiplier": 1.2
    },

    3: {
        "roles": {
            "Data Engineer": (32, 185000),
            "Data Scientist": (20, 195000),
            "Engineering Manager": (4, 235000)
        },
        "cloud_multiplier": 1.4
    },

    4: {
        "roles": {
            "ML Engineer": (25, 205000),
            "Data Scientist": (18, 200000),
            "Engineering Manager": (4, 245000)
        },
        "cloud_multiplier": 1.8
    },

    5: {
        "roles": {
            "Security Engineer": (28, 195000),
            "Software Engineer": (18, 190000),
            "Engineering Manager": (3, 240000)
        },
        "cloud_multiplier": 0.9
    }
}

# -----------------------------
# 6. GENERATE HEADCOUNT DATA
# -----------------------------
headcount_rows = []

for month_index, month in enumerate(months):

    for team_id, config in team_config.items():

        for role_name, (base_headcount, avg_salary) in config["roles"].items():

            # Gradual hiring growth
            growth = int(month_index / 6)

            # Slight variation
            random_change = int(np.random.choice(
                [-1, 0, 0, 0, 1]
            ))

            headcount = int(max(
                1,
                base_headcount + growth + random_change
            ))

            # Salary inflation
            salary_growth = 1 + (0.03 * (month.year - 2025))

            salary = avg_salary * salary_growth

            bonus_pct = 10

            benefits_pct = 20

            headcount_rows.append(
                (
                    month.date(),
                    int(team_id),
                    str(role_name),
                    int(headcount),
                    float(round(salary, 2)),
                    float(bonus_pct),
                    float(benefits_pct)
                )
            )

cursor.executemany("""
INSERT INTO headcount_costs
(
    month,
    team_id,
    role_name,
    headcount,
    avg_salary,
    bonus_pct,
    benefits_pct
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
""", headcount_rows)

print(f"Inserted {len(headcount_rows)} headcount rows.")

# -----------------------------
# 7. GENERATE CLOUD COSTS
# -----------------------------
cloud_services = {
    "Compute": (900000, 0.08),
    "Storage": (450000, 0.02),
    "Database": (300000, 0.10),
    "Network Transfer": (350000, 0.05),
    "ML/GPU": (50000, 1.20)
}

cloud_rows = []

for month_index, month in enumerate(months):

    for team_id, config in team_config.items():

        multiplier = config["cloud_multiplier"]

        for service, (base_usage, unit_cost) in cloud_services.items():

            # Security team uses little GPU
            if team_id == 5 and service == "ML/GPU":
                service_multiplier = 0.15

            # ML team uses lots of GPU
            elif team_id == 4 and service == "ML/GPU":
                service_multiplier = 3.0

            else:
                service_multiplier = 1.0

            # Usage grows over time
            growth_factor = 1 + (month_index * 0.02)

            # Add noise
            noise = np.random.normal(1.0, 0.06)

            usage = (
                base_usage
                * multiplier
                * service_multiplier
                * growth_factor
                * noise
            )

            # Q3 spike
            if month.month in [7, 8, 9]:
                usage *= 1.12

            actual_cost = usage * unit_cost

            cloud_rows.append(
                (
                    month.date(),
                    team_id,
                    service,
                    round(usage, 2),
                    unit_cost,
                    round(actual_cost, 2)
                )
            )

cursor.executemany("""
INSERT INTO cloud_costs
(
    month,
    team_id,
    service_type,
    usage_units,
    unit_cost,
    actual_cost
)
VALUES (%s, %s, %s, %s, %s, %s)
""", cloud_rows)

print(f"Inserted {len(cloud_rows)} cloud rows.")

# -----------------------------
# 8. GENERATE VENDOR COSTS
# -----------------------------
vendors = [
    ("Datadog", "Monitoring", 22000),
    ("GitHub", "Developer Tools", 15000),
    ("Snowflake", "Data Platform", 55000),
    ("Atlassian", "Developer Tools", 12000),
    ("SecurityVendor", "Security", 18000)
]

vendor_rows = []

for month in months:

    for team_id, config in team_config.items():

        for vendor_name, category, base_cost in vendors:

            cost = base_cost

            # Data team uses more Snowflake
            if vendor_name == "Snowflake" and team_id == 3:
                cost *= 2.2

            # ML team uses more data tooling
            if vendor_name == "Snowflake" and team_id == 4:
                cost *= 1.7

            # Security uses more security tooling
            if vendor_name == "SecurityVendor" and team_id == 5:
                cost *= 2.5

            # Annual price increase
            if month.year == 2026:
                cost *= 1.08

            # Small noise
            cost *= np.random.normal(1.0, 0.03)

            vendor_rows.append(
                (
                    month.date(),
                    team_id,
                    vendor_name,
                    category,
                    round(cost, 2)
                )
            )

cursor.executemany("""
INSERT INTO vendor_costs
(
    month,
    team_id,
    vendor_name,
    category,
    actual_cost
)
VALUES (%s, %s, %s, %s, %s)
""", vendor_rows)

print(f"Inserted {len(vendor_rows)} vendor rows.")

# -----------------------------
# 9. GENERATE BUDGET DATA
# -----------------------------
budget_rows = []

for month in months:

    for team_id, config in team_config.items():

        # Headcount budget
        team_roles = config["roles"]

        annual_headcount_budget = sum(
            base_hc * salary
            for base_hc, salary in team_roles.values()
        )

        monthly_headcount_budget = annual_headcount_budget / 12

        # Cloud budget
        cloud_budget = 180000 * config["cloud_multiplier"]
        if team_id == 4:
            cloud_budget *= 1.45

        # Vendor budget
        vendor_budget = 90000

        # Contractors
        contractor_budget = 75000

        # Other OPEX
        other_opex = 40000

        categories = {
            "Headcount": monthly_headcount_budget,
            "Cloud": cloud_budget,
            "Vendors": vendor_budget,
            "Contractors": contractor_budget,
            "Other OPEX": other_opex
        }

        for category, amount in categories.items():

            # 2026 budget growth
            if month.year == 2026:
                amount *= 1.06

            budget_rows.append(
                (
                    month.date(),
                    team_id,
                    category,
                    round(amount, 2)
                )
            )

cursor.executemany("""
INSERT INTO budget
(
    month,
    team_id,
    cost_category,
    budget_amount
)
VALUES (%s, %s, %s, %s)
""", budget_rows)

print(f"Inserted {len(budget_rows)} budget rows.")

# -----------------------------
# 10. GENERATE DYNAMIC FORECAST DATA
# -----------------------------
forecast_rows = []

# Each scenario has:
# 1. starting level adjustment
# 2. monthly growth assumption
scenarios = {
    "Base": {
        "level_multiplier": 1.00,
        "monthly_growth": 0.008       # ~0.8% monthly
    },
    "High Growth": {
        "level_multiplier": 1.10,
        "monthly_growth": 0.014       # ~1.4% monthly
    },
    "Cost Reduction": {
        "level_multiplier": 0.94,
        "monthly_growth": 0.004       # ~0.4% monthly
    }
}

for month_index, month in enumerate(months):

    for team_id, config in team_config.items():

        # -----------------------------------
        # Calculate realistic headcount base
        # -----------------------------------
        annual_salary_base = sum(
            base_hc * salary
            for base_hc, salary in config["roles"].values()
        )

        # Add 10% bonus + 20% benefits
        monthly_headcount_base = (
            annual_salary_base
            / 12
            * 1.30
        )

        # Base monthly expense categories
        categories = {
            "Headcount": monthly_headcount_base,
            "Cloud": 180000 * config["cloud_multiplier"],
            "Vendors": 90000,
            "Contractors": 75000,
            "Other OPEX": 40000
        }

        for category, base_amount in categories.items():

            for scenario_name, assumptions in scenarios.items():

                level_multiplier = assumptions["level_multiplier"]
                monthly_growth = assumptions["monthly_growth"]

                # Compound monthly growth
                growth_factor = (
                    (1 + monthly_growth) ** month_index
                )

                amount = (
                    base_amount
                    * level_multiplier
                    * growth_factor
                )

                # -----------------------------------
                # Business-specific forecast drivers
                # -----------------------------------

                # ML Infrastructure has higher cloud demand
                if team_id == 4 and category == "Cloud":
                    amount *= 1.25

                # Data Platform also consumes more cloud
                if team_id == 3 and category == "Cloud":
                    amount *= 1.10

                # Q3 infrastructure demand spike
                if (
                    category == "Cloud"
                    and month.month in [7, 8, 9]
                ):
                    amount *= 1.08

                # Annual vendor contract increases
                if (
                    category == "Vendors"
                    and month.year == 2026
                ):
                    amount *= 1.06

                # High-growth scenario assumes faster hiring
                if (
                    category == "Headcount"
                    and scenario_name == "High Growth"
                ):
                    amount *= 1.05

                # Cost-reduction scenario constrains contractors
                if (
                    category == "Contractors"
                    and scenario_name == "Cost Reduction"
                ):
                    amount *= 0.80

                # Cost-reduction scenario includes cloud optimization
                if (
                    category == "Cloud"
                    and scenario_name == "Cost Reduction"
                ):
                    amount *= 0.88

                forecast_rows.append(
                    (
                        month.date(),
                        int(team_id),
                        str(category),
                        float(round(amount, 2)),
                        str(scenario_name)
                    )
                )

cursor.executemany("""
INSERT INTO forecast
(
    month,
    team_id,
    cost_category,
    forecast_amount,
    scenario_name
)
VALUES (%s, %s, %s, %s, %s)
""", forecast_rows)

print(f"Inserted {len(forecast_rows)} forecast rows.")

# -----------------------------
# 11. COMMIT
# -----------------------------
conn.commit()

print("\nAll finance data successfully inserted.")

# -----------------------------
# 12. QUICK VALIDATION
# -----------------------------
for table in [
    "headcount_costs",
    "cloud_costs",
    "vendor_costs",
    "budget",
    "forecast"
]:

    cursor.execute(
        f"SELECT COUNT(*) FROM {table};"
    )

    count = cursor.fetchone()[0]

    print(f"{table}: {count} rows")

cursor.close()
conn.close()

print("\nDone.")