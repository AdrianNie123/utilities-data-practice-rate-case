# Rate Case Analysis

A data pipeline for analyzing California Investor-Owned Utility (IOU) costs, revenues, and operational metrics using FERC Form 1 and EIA-861 data.

## Overview

This project processes financial and operational data for California's three major IOUs:
- **PG&E** (Pacific Gas and Electric)
- **SCE** (Southern California Edison)
- **SDG&E** (San Diego Gas & Electric)

The pipeline extracts, transforms, and combines data from multiple sources to create an analysis-ready dataset covering years 2018-2023.

## Data Sources

### EIA-861 (Energy Information Administration)
- **Location**: `data/EIA/`
- **Files**: `Sales_Ult_Cust_{2018-2023}.xlsx`
- **Content**: Sales, revenue, and customer count data by sector (residential, commercial, industrial)

### FERC Form 1 (Federal Energy Regulatory Commission)
- **Location**: `data/FERC/`
- **Files**: 
  - Operating expenses (Schedule 320)
  - Utility plant summary (Schedule 200)
  - Income statements (Schedule 114)
  - Utility association mapping
- **Content**: Financial statements, O&M expenses by account, rate base data

## Project Structure

```
rate-case-analysis/
├── data/
│   ├── EIA/                    # EIA-861 Excel files
│   ├── FERC/                   # FERC Form 1 parquet files
│   └── processed/              # Output directory
├── src/
│   ├── config.py              # Constants and mappings
│   ├── extract.py             # Data loading functions
│   ├── transform.py           # Transformation functions
│   └── pipeline.py            # Main orchestration
├── requirements.txt
└── README.md
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the complete pipeline:

```
To run the pipeline in the future, activate the virtual environment first:
source venv/bin/activate
python -m src.pipeline
The output is saved to data/processed/analysis_ready.parquet and is ready for analysis.
```

The pipeline will:
1. Extract data from EIA Excel files and FERC parquet files
2. Transform and categorize operating expenses
3. Join FERC and EIA data using utility ID mappings
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

The pipeline includes validation checks:
- Required columns present
- Expected row counts (3 utilities × 6 years)
- No null values in critical columns
- Data type consistency

## Error Handling

The pipeline raises specific exceptions for:
- Missing input files (`FileNotFoundError`)
- Data validation failures (`ValueError`)
- Missing required columns

## Data Limitations

**Note:** FERC Form 1 data from PUDL may have varying completeness across utilities. SCE and SDG&E show lower O&M and rate base values in the source data compared to actual regulatory filings. PG&E data appears most complete. For production use, supplement with direct FERC filings or utility-provided data.

## Revenue Requirement and Bill Impact Modules

### Revenue Requirement (`src/revenue_requirement.py`)

Calculates utility revenue requirement using standard regulatory formula:

```
Revenue Requirement = O&M + Depreciation + Return on Rate Base + Taxes
```

**Assumptions (documented in code):**
- Depreciation rate: 3.5% of rate base (~30-year asset life)
- WACC: 7.5% (approximates CPUC-authorized returns)
- Tax rate: 27% (federal 21% + state 6%)

Key functions:
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

The `src/visualize.py` module generates professional charts for regulatory staff reports.

### Available Charts

1. **O&M Trend** (`plot_om_trend`): Line chart showing O&M trends 2018-2023 with CAGR
2. **Peer Comparison** (`plot_peer_comparison`): Horizontal bar chart of cost per customer
3. **RR Waterfall** (`plot_rr_waterfall`): Waterfall chart of revenue requirement components
4. **Revenue Gap** (`plot_revenue_gap`): Bar chart comparing RR to actual revenue
5. **Bill Impact** (`plot_bill_impact`): Grouped bar chart of current vs projected bills
6. **YoY Heatmap** (`plot_yoy_heatmap`): Heatmap of year-over-year O&M changes

### Running Visualizations

```bash
python -m src.visualize
```

All figures are saved to `outputs/figures/` at 300 dpi PNG format.

### Color Scheme
- PG&E: #1f77b4 (blue)
- SCE: #ff7f0e (orange)
- SDG&E: #2ca02c (green)

## Analysis Module

The `src/analyze.py` module provides comprehensive analysis functions:

### Available Functions

1. **Trend Analysis** (`trend_analysis`): Calculates linear regression, CAGR, and descriptive statistics for a utility and metric
2. **Cost Driver Regression** (`cost_driver_regression`): OLS regression of O&M costs on customers, sales, and rate base
3. **Outlier Detection** (`detect_outliers`): Z-score based outlier identification
4. **Peer Benchmarking** (`peer_benchmark`): Utility rankings and percentiles for a given year
5. **Year-over-Year Change** (`calculate_yoy_change`): Calculates YoY percent changes
6. **Summary Statistics** (`summary_by_utility`): Aggregated statistics by utility
7. **Run All Analyses** (`run_analysis`): Orchestrates all analyses and returns results

### Running Analysis

```bash
python3 -c run_analysis.py
```

This will:
- Load the analysis-ready dataset
- Execute all analyses
- Print key findings
- Save results to `data/processed/analysis_results.json`

### Key Findings Output

The analysis prints:
- Highest O&M per customer utility
- Fastest cost growth (CAGR)
- Statistically significant cost drivers
- Detected outlier years

## License

This project is for regulatory analysis purposes.

visualization:
python3 -c "from src.visualize import generate_all_figures; generate_all_figures()"
