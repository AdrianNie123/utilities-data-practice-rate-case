# Project: Utilities Analysis (Rate Case Data)

A data pipeline for analyzing California Investor-Owned Utility (IOU) costs, revenues, and operational metrics using FERC Form 1 and EIA-861 data.

## Overview

This project processes financial and operational data for California's three major IOUs:
- **PG&E** (Pacific Gas and Electric)
- **SCE** (Southern California Edison)
- **SDG&E** (San Diego Gas & Electric)

The pipeline extracts, transforms, and combines data from multiple sources to create an analysis-ready dataset covering years 2018-2023.

## Data Sources

### EIA-861 (Energy Information Administration)
- **Files**: `Sales_Ult_Cust_{2018-2023}.xlsx`
- **Content**: Sales, revenue, and customer count data by sector (residential, commercial, industrial)

### FERC Form 1 (Federal Energy Regulatory Commission)
- **Files**: 
  - Op. expenses (Schedule 320)
  - Utility plant summary (Schedule 200)
  - Income statements (Schedule 114)
- **Content**: Financial statements, O&M expenses by account, rate base data

## Project Structure

```
rate-case-analysis/
├── practice-notebooks/
├── data/
│   ├── EIA/                    # EIA-861 Excel files
│   ├── FERC/                   # FERC Form 1 parquet files
│   └── processed/              # Output directory
├── src/
|   ├── analyze.py             # Analyze and summarize data
|   ├── bill_impact.py         # Customer Impact and bill impact analysis
|   ├── revenue_requirement.py # Calc RR, OM, Mock Rate Base,..
│   ├── config.py              # Constants and mappings
│   ├── extract.py             # Data loading funcs
│   ├── transform.py           # Transformation funcs
|   ├── visualize.py           # Visualizations MatPlotLib
│   └── pipeline.py            # Main
├── requirements.txt
└── README.md
```


Data pipeline 
1. Extract data from EIA Excel files and FERC parquet files
2. Transform and categorize operating expenses
3. Join FERC and EIA data w/ utility ID mappings
4. Derive calculated metrics (O&M per customer, O&M per MWh, etc.)
5. Export to `data/processed/analysis_ready.parquet`

## Output Schema

The final dataset (`analysis_ready.parquet`) contains the following columns:

| Column | Type | Description |
|--------|------|-------------|
| utility_id_ferc1 | int | FERC utility ID |
| utility_id_eia | int | EIA utility ID |
| utility_name | str | Utility name (PG&E, SCE, SDG&E) |
| report_year | int | Report year (2018-2023) |
| om_production | float | Production O&M expenses ($) |
| om_transmission | float | Transmission O&M expenses ($) |
| om_distribution | float | Distribution O&M expenses ($) |
| om_customer_service | float | Customer service O&M expenses ($) |
| om_admin_general | float | Admin & general O&M expenses ($) |
| om_other | float | Other O&M expenses ($) |
| om_total | float | Total O&M expenses ($) |
| rate_base | float | Net rate base ($) |
| sales_mwh_total | float | Total MWh sold |
| customers_total | int | Total customer count |
| revenue_total_k | float | Total revenue ($000) |
| om_per_customer | float | O&M per customer ($) |
| om_per_mwh | float | O&M per MWh ($) |
| rate_base_per_customer | float | Rate base per customer ($) |
| revenue_per_customer | float | Revenue per customer ($) |

## FERC Account Categorization

Operating expenses are categorized by FERC account code ranges:
- **Production** (500-554): Power generation expenses
- **Transmission** (560-574): Transmission system expenses
- **Distribution** (580-598): Distribution system expenses
- **Customer Service** (901-910): Customer-facing operations
- **Admin & General** (920-935): Administrative and general expenses
- **Other**: All other account codes

## Data Validation

Data pipeline includes validation checks:
- Required columns present
- Expected row counts (3 utilities × 6 years)
- No null values in critical columns
- Data type consistency

## Error Handling

Built pipeline to raise specific exceptions for:
- Missing input files (`FileNotFoundError`)
- Data validation failures (`ValueError`)
- Missing required columns

## Data Limitations

- No confidential paperwork > Can't verify item costs, specific projects/contracts
    - Used aggregate categories; analysis serves mainly as baseline check not detailed audit
 

## Revenue Requirement and Bill Impact Modules

### Revenue Requirement (`src/revenue_requirement.py`)

Calculates utility revenue requirement using standard regulatory formula:

```
Revenue Requirement = O&M + Depreciation + Return on Rate Base + Taxes* (* Source: [Google](https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/electric-costs))
```

**Assumptions (documented in code):**
- Depreciation rate: 3.5% of rate base (~30-year asset life)
- WACC: 7.5% (approximates CPUC-authorized returns)
- Tax rate: 27% (federal 21% + state 6%)
- Forecast review -> used historical actuals + standard escalaton (EIA-861), cant directly evaluate proposals

Note functions:
- `calculate_revenue_requirement()`: Single utility-year calculation
- `apply_rr_to_dataset()`: Apply to full dataset with revenue gap analysis
- `forecast_test_year()`: Project RR with escalation factors

### Bill Impact (`src/bill_impact.py`)

Estimates residential monthly bill changes:

- `calculate_class_shares()`: Revenue shares from actual EIA data
- `calculate_residential_bill()`: Average monthly bill calculation
- `bill_impact_analysis()`: Current vs. proposed bill comparison
- `sensitivity_analysis()`: Test multiple scenarios

**Output Files:**
- `data/processed/revenue_requirement.parquet`: RR by utility-year
- `data/processed/bill_impact.parquet`: Bill impact by utility

## Visualization Module

 `src/visualize.py` module that generates charts from reports.

### Attached Charts Below

1. **O&M Trend (2018-2023)** 
2. **Peer Comparison** 
3. **RR Waterfall** 
4. **Revenue Gap** 
5. **Bill Impact** 
6. **YoY Heatmap** 

## Analysis Module

 `src/analyze.py` module: comprehensive analysis functions

### Demonstrated Functions Below

1. **Trend Analysis** : Calculates linear regression, CAGR, and descriptive statistics for a utility and metric
2. **Cost Driver Regression** : OLS regression of O&M costs on customers, sales, and rate base
3. **Outlier Detection** : Z-score based outlier identification
4. **Peer Benchmarking** : Utility rankings and percentiles for a given year
5. **Year-over-Year Change** : Calculates YoY percent changes
6. **Summary Statistics** : Aggregated statistics by utility
7. **Run All Analyses** : Orchestrates all analyses and returns results

### Key Findings Output

The analysis prints:
- Highest O&M per customer utility
- Fastest cost growth (CAGR)
- Statistically significant cost drivers
- Detected outlier years


visualization function:
python3 -c "from src.visualize import generate_all_figures; generate_all_figures()"
