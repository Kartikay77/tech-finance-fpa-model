# Tech Finance FP&A Model

A driver-based Technology FP&A and strategic finance model for analyzing engineering headcount, cloud infrastructure spend, vendor costs, budget-to-actual performance, and multi-scenario forecasts.

The project combines **MySQL, Python, and Google Sheets** to simulate a technology finance planning workflow and produce management-ready insights for engineering and finance leadership.

## Business Problem

Technology organizations need to understand how engineering headcount, cloud capacity, and third-party tooling affect operating expenses while planning for different growth scenarios.

This project models a Technology Finance organization supporting five engineering cost centers:

- Payments Engineering
- Marketplace Platform
- Data Platform
- ML Infrastructure
- Security Engineering

The model evaluates historical operating expenses, budget performance, cost drivers, and forward-looking scenarios across 2025–2026.

## Tech Stack

- **MySQL** — financial data model and analytical queries
- **Python** — synthetic data generation, FP&A calculations, scenario analysis
- **Pandas / NumPy** — financial analysis and data transformation
- **Google Sheets** — management reporting and dashboarding

## Financial Model

The model tracks three primary Technology OPEX components:

- Headcount compensation
- Cloud infrastructure
- Software and vendor expenses

Headcount costs include:

- Base salary
- Bonus
- Benefits

Cloud spending models:

- Compute
- Storage
- Databases
- Network transfer
- ML / GPU infrastructure

## Scenario Planning

Three forward-looking scenarios are modeled:

### Base Case
Represents continued operating growth under expected hiring and infrastructure demand.

### High Growth
Models accelerated engineering investment, hiring, and cloud capacity expansion.

### Cost Reduction
Models lower growth combined with cloud optimization and contractor cost reductions.

## Key Results

### Technology OPEX

- **2025 Actual OPEX:** ~$98.9M
- **2026 Actual OPEX:** ~$114.2M
- **YoY OPEX Growth:** ~15.5%

### Cost Mix — 2026

- **Headcount:** ~71.5%
- **Cloud:** ~20.0%
- **Vendors:** ~8.4%

Headcount remains the largest Technology OPEX driver while cloud infrastructure becomes a larger share of total spending.

### 2026 Scenario Analysis

- **Base Forecast:** ~$111.8M
- **Cost Reduction Scenario:** ~$95.2M
- **High Growth Scenario:** ~$141.4M
- **Potential Savings vs Base:** ~$16.5M
- **Incremental High-Growth Spend:** ~$29.6M

### Cost Center Analysis

ML Infrastructure is the largest modeled 2026 cost center at approximately **$26.5M**, with cloud infrastructure representing a significant portion of its spending.

## Analysis Performed

The project includes:

- Monthly Technology OPEX analysis
- Budget vs actual variance analysis
- Engineering cost-center analysis
- Headcount cost planning
- Cloud spend analysis
- Annual cost mix analysis
- Scenario forecasting
- Cost-reduction opportunity analysis
- Management reporting

## Dashboard Views

The Google Sheets FP&A dashboard includes:

- Executive Summary
- Actual OPEX trends
- Budget vs Actual
- Forecast scenarios
- Headcount analysis
- Cloud cost analysis
- Technology OPEX cost mix

Example management metrics include:

- Total OPEX
- YoY growth
- Budget variance
- Cloud spend
- Headcount costs
- Scenario savings
- Incremental growth investment

## Repository Structure

```text
tech-finance-fpa-model/
│
├── README.md
│
├── sql/
│   └── techfinance_schema_and_analysis.sql
│
├── python/
│   ├── uber_techfinance.py
│   ├── analyze_techfinance.py
│   └── management_summary.py
│
├── data/
│   ├── monthly_actual_opex.csv
│   ├── annual_team_opex.csv
│   ├── annual_cost_mix.csv
│   ├── forecast_scenario_analysis.csv
│   └── cloud_budget_variance.csv
│
└── dashboard/
    └── screenshots/

Data Model
The MySQL model contains the following core tables:
- teams
- headcount_costs
- cloud_costs
- vendor_costs
- budget
- forecast
These tables support monthly financial planning and reporting across engineering cost centers.
Example SQL Analysis
The SQL layer supports queries for:
- Monthly cloud spend
- Cloud budget vs actual variance
- Fully loaded headcount costs
- Team-level Technology OPEX
- Monthly actual OPEX
- Annual team OPEX
- Forecast scenario comparison
Management Insights
The analysis highlights several strategic finance considerations:
1. Headcount is the largest controllable cost base, accounting for roughly 72% of Technology OPEX.
2. Cloud spending is growing faster than other cost categories, increasing its share of overall OPEX.
3. ML Infrastructure is the largest Technology cost center, driven partly by infrastructure-intensive workloads.
4. Scenario analysis indicates that targeted efficiency measures could reduce modeled 2026 spending by approximately $16.5M relative to the Base case.
5. A High Growth strategy would require approximately $29.6M of incremental investment relative to Base.
Disclaimer
This project uses synthetic financial and operational data created for portfolio and analytical demonstration purposes. It does not contain or represent confidential financial information from Uber or any other company.
