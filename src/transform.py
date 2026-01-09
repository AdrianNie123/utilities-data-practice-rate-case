"""Data transformation functions for Rate Case Analysis pipeline."""

import pandas as pd
from typing import Dict, List, Optional, Union

from src.config import (
    FERC_ACCOUNT_CATEGORIES,
    UTILITY_MAPPING,
)


def categorize_ferc_account(ferc_account: str) -> str:
    """
    Categorize FERC account code into functional category.

    Args:
        ferc_account: FERC account code (e.g., "500", "920.1")

    Returns:
        Category name or "other"
    """
    try:
        # Extract integer prefix (before decimal if present)
        account_prefix: int = int(float(ferc_account))
    except (ValueError, TypeError):
        return "other"
    
    # Check each category range
    for category, (min_val, max_val) in FERC_ACCOUNT_CATEGORIES.items():
        if min_val <= account_prefix <= max_val:
            return category
    
    return "other"


def categorize_operating_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add category column to operating expenses DataFrame.

    Args:
        df: Operating expenses DataFrame with ferc_account column

    Returns:
        DataFrame with category column added
    """
    df_copy: pd.DataFrame = df.copy()
    df_copy["category"] = df_copy["ferc_account"].astype(str).apply(categorize_ferc_account)
    return df_copy


def pivot_expenses_to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot operating expenses from long to wide format.

    Creates columns: om_production, om_transmission, om_distribution,
    om_customer_service, om_admin_general, om_other, om_total

    Args:
        df: Operating expenses DataFrame with category column

    Returns:
        Wide format DataFrame with one row per utility-year
    """
    # Sum expenses by utility, year, and category
    grouped: pd.DataFrame = df.groupby(
        ["utility_id_ferc1", "report_year", "category"],
        as_index=False
    )["dollar_value"].sum()
    
    # Pivot to wide format
    pivoted: pd.DataFrame = grouped.pivot_table(
        index=["utility_id_ferc1", "report_year"],
        columns="category",
        values="dollar_value",
        fill_value=0.0
    ).reset_index()
    
    # Rename columns to include om_ prefix
    column_mapping: Dict[str, str] = {
        col: f"om_{col}" for col in pivoted.columns if col not in ["utility_id_ferc1", "report_year"]
    }
    pivoted = pivoted.rename(columns=column_mapping)
    
    # Ensure all category columns exist
    expected_categories: List[str] = [
        "om_production",
        "om_transmission",
        "om_distribution",
        "om_customer_service",
        "om_admin_general",
        "om_other",
    ]
    
    for col in expected_categories:
        if col not in pivoted.columns:
            pivoted[col] = 0.0
    
    # Calculate total
    pivoted["om_total"] = pivoted[expected_categories].sum(axis=1)
    
    return pivoted


def calculate_rate_base(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate rate base from utility plant data.

    rate_base = utility_plant_in_service - accumulated_provision_for_depreciation

    Args:
        df: Utility plant DataFrame

    Returns:
        DataFrame with rate_base column added
    """
    df_copy: pd.DataFrame = df.copy()
    df_copy["rate_base"] = (
        df_copy["utility_plant_in_service"] - 
        df_copy["accumulated_provision_for_depreciation"]
    )
    return df_copy


def create_ferc_eia_mapping() -> pd.DataFrame:
    """
    Create mapping DataFrame between FERC and EIA utility IDs.

    Returns:
        DataFrame with utility_id_ferc1, utility_id_eia, and utility_name columns
    """
    mapping_data: List[Dict[str, Union[int, str]]] = []
    
    for utility_name, (ferc_id, eia_id) in UTILITY_MAPPING.items():
        mapping_data.append({
            "utility_id_ferc1": ferc_id,
            "utility_id_eia": eia_id,
            "utility_name": utility_name,
        })
    
    return pd.DataFrame(mapping_data)


def join_ferc_eia_data(
    ferc_expenses: pd.DataFrame,
    ferc_plant: pd.DataFrame,
    eia_data: pd.DataFrame,
    ferc_revenues: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Join FERC and EIA data using utility ID mapping.

    Args:
        ferc_expenses: FERC operating expenses (wide format)
        ferc_plant: FERC utility plant data with rate_base
        eia_data: EIA sales and customer data
        ferc_revenues: FERC operating revenues from schedule 114 (optional)

    Returns:
        Joined DataFrame
    """
    # Create mapping
    mapping: pd.DataFrame = create_ferc_eia_mapping()
    
    # Join expenses with plant data
    ferc_combined: pd.DataFrame = ferc_expenses.merge(
        ferc_plant[["utility_id_ferc1", "report_year", "rate_base"]],
        on=["utility_id_ferc1", "report_year"],
        how="outer"
    )
    
    # Join with operating revenues if provided
    if ferc_revenues is not None:
        ferc_combined = ferc_combined.merge(
            ferc_revenues[["utility_id_ferc1", "report_year", "operating_revenues_ferc"]],
            on=["utility_id_ferc1", "report_year"],
            how="left"
        )
    
    # Join with mapping to get EIA ID
    ferc_with_eia: pd.DataFrame = ferc_combined.merge(
        mapping,
        on="utility_id_ferc1",
        how="left"
    )
    
    # Join with EIA data
    final: pd.DataFrame = ferc_with_eia.merge(
        eia_data,
        on=["utility_id_eia", "report_year"],
        how="outer"
    )
    
    # Ensure utility_name is populated from mapping if missing
    final["utility_name"] = final["utility_name_x"].fillna(final["utility_name_y"])
    final = final.drop(columns=["utility_name_x", "utility_name_y"], errors="ignore")
    
    return final


def derive_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive calculated metrics from base data.

    Calculates:
    - grc_om = Distribution + Customer Service + (A&G × 70%)
    - om_per_customer = om_total / customers_total
    - grc_om_per_customer = grc_om / customers_total (GRC-comparable)
    - om_per_mwh = om_total / sales_mwh_total
    - rate_base_per_customer = rate_base / customers_total
    - revenue_per_customer = (revenue_total_k * 1000) / customers_total

    Args:
        df: Combined DataFrame with base metrics

    Returns:
        DataFrame with derived metrics added
    """
    df_copy: pd.DataFrame = df.copy()
    
    # GRC-comparable O&M (excludes production, transmission, 30% A&G)
    # Only CPUC-regulated costs: Distribution + Customer Service + (A&G × 70%)
    ag_allocation: float = 0.70  # 70% electric allocation
    df_copy["grc_om"] = (
        df_copy["om_distribution"] +
        df_copy["om_customer_service"] +
        (df_copy["om_admin_general"] * ag_allocation)
    )
    
    # om_per_customer (total O&M basis)
    df_copy["om_per_customer"] = df_copy["om_total"] / df_copy["customers_total"].replace(0, pd.NA)
    
    # grc_om_per_customer (GRC-comparable basis - for peer comparison)
    df_copy["grc_om_per_customer"] = df_copy["grc_om"] / df_copy["customers_total"].replace(0, pd.NA)
    
    # om_per_mwh
    df_copy["om_per_mwh"] = df_copy["om_total"] / df_copy["sales_mwh_total"].replace(0, pd.NA)
    
    # rate_base_per_customer
    df_copy["rate_base_per_customer"] = df_copy["rate_base"] / df_copy["customers_total"].replace(0, pd.NA)
    
    # revenue_per_customer
    df_copy["revenue_per_customer"] = (df_copy["revenue_total_k"] * 1000) / df_copy["customers_total"].replace(0, pd.NA)
    
    return df_copy


def select_final_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select and order final output columns.

    Args:
        df: DataFrame with all columns

    Returns:
        DataFrame with selected columns in order
    """
    final_columns: List[str] = [
        "utility_id_ferc1",
        "utility_id_eia",
        "utility_name",
        "report_year",
        "om_production",
        "om_transmission",
        "om_distribution",
        "om_customer_service",
        "om_admin_general",
        "om_other",
        "om_total",
        "grc_om",
        "rate_base",
        "operating_revenues_ferc",
        "sales_mwh_residential",
        "sales_mwh_commercial",
        "sales_mwh_industrial",
        "sales_mwh_total",
        "customers_residential",
        "customers_commercial",
        "customers_industrial",
        "customers_total",
        "revenue_residential_k",
        "revenue_commercial_k",
        "revenue_industrial_k",
        "revenue_total_k",
        "om_per_customer",
        "grc_om_per_customer",
        "om_per_mwh",
        "rate_base_per_customer",
        "revenue_per_customer",
    ]
    
    # Only select columns that exist
    available_columns: List[str] = [col for col in final_columns if col in df.columns]
    
    return df[available_columns].copy()


def validate_output(df: pd.DataFrame) -> None:
    """
    Validate output DataFrame for data quality.

    Args:
        df: Output DataFrame

    Raises:
        ValueError: If validation fails
    """
    if df.empty:
        raise ValueError("Output DataFrame is empty")
    
    # Check required columns
    required_columns: List[str] = [
        "utility_id_ferc1",
        "utility_id_eia",
        "utility_name",
        "report_year",
        "om_total",
    ]
    
    missing_columns: List[str] = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Check for expected number of rows (3 utilities * 6 years = 18)
    expected_rows: int = len(UTILITY_MAPPING) * len([2018, 2019, 2020, 2021, 2022, 2023])
    if len(df) < expected_rows * 0.5:  # Allow some missing data
        raise ValueError(f"Unexpectedly low row count: {len(df)} (expected at least {expected_rows * 0.5})")
    
    # Check for nulls in critical columns
    critical_columns: List[str] = ["utility_id_ferc1", "utility_id_eia", "report_year"]
    for col in critical_columns:
        null_count: int = df[col].isna().sum()
        if null_count > 0:
            raise ValueError(f"Found {null_count} null values in critical column: {col}")

