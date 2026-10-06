-- ============================================================
-- Tech Finance FP&A Model
-- MySQL schema + core analysis queries
-- ============================================================

-- 1. DATABASE
CREATE DATABASE IF NOT EXISTS techfinance;
USE techfinance;

-- ============================================================
-- 2. DIMENSION TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS teams (
    team_id INT PRIMARY KEY AUTO_INCREMENT,
    team_name VARCHAR(100) NOT NULL,
    function_name VARCHAR(100),
    manager_name VARCHAR(100),
    cost_center VARCHAR(50)
);

INSERT INTO teams (team_name, function_name, manager_name, cost_center)
VALUES
    ('Payments Engineering', 'Engineering', 'Manager A', 'ENG-PAY'),
    ('Marketplace Platform', 'Engineering', 'Manager B', 'ENG-MKT'),
    ('Data Platform', 'Engineering', 'Manager C', 'ENG-DATA'),
    ('ML Infrastructure', 'Engineering', 'Manager D', 'ENG-ML'),
    ('Security Engineering', 'Engineering', 'Manager E', 'ENG-SEC')
ON DUPLICATE KEY UPDATE
    team_name = VALUES(team_name);

-- ============================================================
-- 3. FACT TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS headcount_costs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    month DATE NOT NULL,
    team_id INT NOT NULL,
    role_name VARCHAR(100),
    headcount INT,
    avg_salary DECIMAL(12,2),
    bonus_pct DECIMAL(5,2),
    benefits_pct DECIMAL(5,2),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS cloud_costs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    month DATE NOT NULL,
    team_id INT NOT NULL,
    service_type VARCHAR(100),
    usage_units DECIMAL(14,2),
    unit_cost DECIMAL(10,4),
    actual_cost DECIMAL(14,2),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS vendor_costs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    month DATE NOT NULL,
    team_id INT NOT NULL,
    vendor_name VARCHAR(100),
    category VARCHAR(100),
    actual_cost DECIMAL(14,2),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS budget (
    id INT PRIMARY KEY AUTO_INCREMENT,
    month DATE NOT NULL,
    team_id INT NOT NULL,
    cost_category VARCHAR(100),
    budget_amount DECIMAL(14,2),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS forecast (
    id INT PRIMARY KEY AUTO_INCREMENT,
    month DATE NOT NULL,
    team_id INT NOT NULL,
    cost_category VARCHAR(100),
    forecast_amount DECIMAL(14,2),
    scenario_name VARCHAR(50),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- ============================================================
-- 4. INDEXES
-- ============================================================

CREATE INDEX idx_headcount_month_team
    ON headcount_costs(month, team_id);

CREATE INDEX idx_cloud_month_team
    ON cloud_costs(month, team_id);

CREATE INDEX idx_vendor_month_team
    ON vendor_costs(month, team_id);

CREATE INDEX idx_budget_month_team_category
    ON budget(month, team_id, cost_category);

CREATE INDEX idx_forecast_month_scenario
    ON forecast(month, scenario_name);

-- ============================================================
-- 5. ANALYSIS QUERIES
-- ============================================================

-- ------------------------------------------------------------
-- A. Monthly total cloud spend
-- ------------------------------------------------------------
SELECT
    month,
    ROUND(SUM(actual_cost), 2) AS total_cloud_spend
FROM cloud_costs
GROUP BY month
ORDER BY month;

-- ------------------------------------------------------------
-- B. Monthly cloud spend by engineering team
-- ------------------------------------------------------------
SELECT
    c.month,
    t.team_name,
    ROUND(SUM(c.actual_cost), 2) AS cloud_spend
FROM cloud_costs c
JOIN teams t
    ON c.team_id = t.team_id
GROUP BY
    c.month,
    t.team_name
ORDER BY
    c.month,
    cloud_spend DESC;

-- ------------------------------------------------------------
-- C. Cloud budget vs actual variance
-- ------------------------------------------------------------
SELECT
    b.month,
    t.team_name,
    b.budget_amount,
    ROUND(SUM(c.actual_cost), 2) AS actual_amount,
    ROUND(SUM(c.actual_cost) - b.budget_amount, 2) AS variance_amount,
    ROUND(
        (SUM(c.actual_cost) - b.budget_amount)
        / b.budget_amount * 100,
        2
    ) AS variance_pct
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

-- ------------------------------------------------------------
-- D. Monthly fully loaded headcount cost
-- ------------------------------------------------------------
SELECT
    h.month,
    t.team_name,
    ROUND(
        SUM(
            h.headcount
            * h.avg_salary
            / 12
            * (1 + h.bonus_pct / 100 + h.benefits_pct / 100)
        ),
        2
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

-- ------------------------------------------------------------
-- E. Monthly team-level Technology OPEX
--    Includes headcount + cloud + vendors
-- ------------------------------------------------------------
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
    ROUND(hc.headcount_cost, 2) AS headcount_cost,
    ROUND(cloud.cloud_cost, 2) AS cloud_cost,
    ROUND(vendor.vendor_cost, 2) AS vendor_cost,
    ROUND(
        hc.headcount_cost
        + cloud.cloud_cost
        + vendor.vendor_cost,
        2
    ) AS total_tech_opex
FROM hc
JOIN cloud
    ON hc.month = cloud.month
    AND hc.team_id = cloud.team_id
JOIN vendor
    ON hc.month = vendor.month
    AND hc.team_id = vendor.team_id
JOIN teams t
    ON hc.team_id = t.team_id
ORDER BY
    hc.month,
    total_tech_opex DESC;

-- ------------------------------------------------------------
-- F. Forecast scenario comparison by month
-- ------------------------------------------------------------
SELECT
    month,
    scenario_name,
    ROUND(SUM(forecast_amount), 2) AS total_forecast
FROM forecast
GROUP BY
    month,
    scenario_name
ORDER BY
    month,
    scenario_name;

-- ------------------------------------------------------------
-- G. Annual forecast scenario summary
-- ------------------------------------------------------------
SELECT
    YEAR(month) AS year,
    scenario_name,
    ROUND(SUM(forecast_amount), 2) AS annual_forecast
FROM forecast
GROUP BY
    YEAR(month),
    scenario_name
ORDER BY
    year,
    scenario_name;

-- ------------------------------------------------------------
-- H. Monthly actual Technology OPEX
-- ------------------------------------------------------------
WITH hc AS (
    SELECT
        month,
        SUM(
            headcount
            * avg_salary
            / 12
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
    ROUND(hc.headcount_cost, 2) AS headcount_cost,
    ROUND(cloud.cloud_cost, 2) AS cloud_cost,
    ROUND(vendor.vendor_cost, 2) AS vendor_cost,
    ROUND(
        hc.headcount_cost
        + cloud.cloud_cost
        + vendor.vendor_cost,
        2
    ) AS total_actual_opex
FROM hc
JOIN cloud
    ON hc.month = cloud.month
JOIN vendor
    ON hc.month = vendor.month
ORDER BY hc.month;

-- ------------------------------------------------------------
-- I. Annual OPEX by team
-- ------------------------------------------------------------
WITH monthly_team_opex AS (
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
        hc.team_id,
        hc.headcount_cost,
        cloud.cloud_cost,
        vendor.vendor_cost
    FROM hc
    JOIN cloud
        ON hc.month = cloud.month
        AND hc.team_id = cloud.team_id
    JOIN vendor
        ON hc.month = vendor.month
        AND hc.team_id = vendor.team_id
)
SELECT
    YEAR(m.month) AS year,
    t.team_name,
    ROUND(SUM(m.headcount_cost), 2) AS headcount_cost,
    ROUND(SUM(m.cloud_cost), 2) AS cloud_cost,
    ROUND(SUM(m.vendor_cost), 2) AS vendor_cost,
    ROUND(
        SUM(
            m.headcount_cost
            + m.cloud_cost
            + m.vendor_cost
        ),
        2
    ) AS total_opex
FROM monthly_team_opex m
JOIN teams t
    ON m.team_id = t.team_id
GROUP BY
    YEAR(m.month),
    t.team_name
ORDER BY
    year,
    total_opex DESC;

-- ============================================================
-- Notes
-- ============================================================
-- Fact data is generated by the accompanying Python pipeline.
-- The SQL layer stores planning/actual data and supports FP&A
-- analysis for headcount, cloud spend, vendor spend, budget
-- variance, and scenario forecasting.
