"""Configuration constants and mappings for Rate Case Analysis pipeline."""

from pathlib import Path
from typing import Dict, List, Tuple

# Project root directory
PROJECT_ROOT: Path = Path(__file__).parent.parent

# Data directories
DATA_RAW: Path = PROJECT_ROOT / "data"
DATA_EIA: Path = DATA_RAW / "EIA"
DATA_FERC: Path = DATA_RAW / "FERC"
DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"

# Output file
OUTPUT_FILE: Path = DATA_PROCESSED / "analysis_ready.parquet"

# Target utilities: (FERC ID, EIA ID)
# Correct FERC IDs from PUDL data:
# - PG&E: 183 (Pacific Gas and Electric Company)
# - SCE: 155 (Southern California Edison Company)
# - SDG&E: 218 (San Diego Gas & Electric Company)
UTILITY_MAPPING: Dict[str, Tuple[int, int]] = {
    "PG&E": (183, 14328),
    "SCE": (155, 17609),
    "SDG&E": (218, 16609),
}

# Years to process
YEARS: List[int] = [2018, 2019, 2020, 2021, 2022, 2023]

# EIA file pattern
EIA_FILE_PATTERN: str = "Sales_Ult_Cust_{year}.xlsx"

# EIA column mapping (original -> standardized)
EIA_COLUMN_MAPPING: Dict[str, str] = {
    "Data Year": "report_year",
    "Utility Number": "utility_id_eia",
    "Utility Name": "utility_name",
    "State": "state",
    "Ownership": "ownership",
    "Thousand Dollars": "revenue_residential_k",
    "Megawatthours": "sales_mwh_residential",
    "Count": "customers_residential",
    "Thousand Dollars.1": "revenue_commercial_k",
    "Megawatthours.1": "sales_mwh_commercial",
    "Count.1": "customers_commercial",
    "Thousand Dollars.2": "revenue_industrial_k",
    "Megawatthours.2": "sales_mwh_industrial",
    "Count.2": "customers_industrial",
    "Thousand Dollars.4": "revenue_total_k",
    "Megawatthours.4": "sales_mwh_total",
    "Count.4": "customers_total",
}

# FERC account category mapping
# Maps account code prefix to category
FERC_ACCOUNT_CATEGORIES: Dict[str, Tuple[int, int]] = {
    "production": (500, 557),
    "transmission": (560, 574),
    "distribution": (580, 598),
    "customer_service": (901, 910),
    "admin_general": (920, 935),
}

# FERC file names
FERC_OPERATING_EXPENSES: str = "core_ferc1__yearly_operating_expenses_sched320.parquet"
FERC_UTILITY_PLANT: str = "core_ferc1__yearly_utility_plant_summary_sched200.parquet"
FERC_INCOME_STATEMENTS: str = "core_ferc1__yearly_income_statements_sched114.parquet"
FERC_UTILITY_ASSOCIATION: str = "core_pudl__assn_ferc1_pudl_utilities.parquet"

# Target state
TARGET_STATE: str = "CA"

# Utility type filter
UTILITY_TYPE_ELECTRIC: str = "electric"
