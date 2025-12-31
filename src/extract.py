"""Data extraction functions for EIA-861 and FERC Form 1 data."""

import pandas as pd
from pathlib import Path
from typing import Dict, List

from src.config import (
    DATA_EIA,
    DATA_FERC,
    EIA_FILE_PATTERN,
    EIA_COLUMN_MAPPING,
    YEARS,
    UTILITY_MAPPING,
    TARGET_STATE,
    UTILITY_TYPE_ELECTRIC,
    FERC_OPERATING_EXPENSES,
    FERC_UTILITY_PLANT,
    FERC_INCOME_STATEMENTS,
    FERC_UTILITY_ASSOCIATION,
)


def load_eia_file(year: int) -> pd.DataFrame:
    """
    Load a single EIA-861 Sales_Ult_Cust Excel file.

    Args:
        year: Report year (2018-2023)

    Returns:
        DataFrame with standardized column names

    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path: Path = DATA_EIA / EIA_FILE_PATTERN.format(year=year)
    
    if not file_path.exists():
        raise FileNotFoundError(f"EIA file not found: {file_path}")
    
    df: pd.DataFrame = pd.read_excel(
        file_path,
        skiprows=2,
        engine="openpyxl"
    )
    
    # Rename columns
    df = df.rename(columns=EIA_COLUMN_MAPPING)
    
    # Filter to only include columns that exist
    available_columns: List[str] = [col for col in EIA_COLUMN_MAPPING.values() if col in df.columns]
    df = df[available_columns]
    
    return df


def extract_eia_data() -> pd.DataFrame:
    """
    Extract and combine all EIA-861 files.

    Returns:
        Combined DataFrame with all years

    Raises:
        ValueError: If no data is loaded or required columns are missing
    """
    all_data: List[pd.DataFrame] = []
    
    for year in YEARS:
        df: pd.DataFrame = load_eia_file(year)
        all_data.append(df)
    
    combined: pd.DataFrame = pd.concat(all_data, ignore_index=True)
    
    # Validate required columns
    required_columns: List[str] = ["report_year", "utility_id_eia", "state"]
    missing_columns: List[str] = [col for col in required_columns if col not in combined.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    return combined


def filter_eia_to_ca_ious(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter EIA data to California IOUs.

    Args:
        df: EIA DataFrame

    Returns:
        Filtered DataFrame
    """
    # Get target EIA IDs
    target_eia_ids: List[int] = [mapping[1] for mapping in UTILITY_MAPPING.values()]
    
    filtered: pd.DataFrame = df[
        (df["state"] == TARGET_STATE) &
        (df["utility_id_eia"].isin(target_eia_ids))
    ].copy()
    
    return filtered


def aggregate_eia_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate EIA data by utility_id_eia and report_year.

    Sums numeric columns and keeps first value for string columns.

    Args:
        df: EIA DataFrame

    Returns:
        Aggregated DataFrame
    """
    # Identify numeric columns (excluding IDs and year)
    numeric_columns: List[str] = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
    numeric_columns = [col for col in numeric_columns if col not in ["utility_id_eia", "report_year"]]
    
    # Identify string columns
    string_columns: List[str] = df.select_dtypes(include=["object"]).columns.tolist()
    
    # Group by utility and year
    agg_dict: Dict[str, str] = {col: "sum" for col in numeric_columns}
    agg_dict.update({col: "first" for col in string_columns})
    
    aggregated: pd.DataFrame = df.groupby(
        ["utility_id_eia", "report_year"],
        as_index=False
    ).agg(agg_dict)
    
    return aggregated


def load_ferc_operating_expenses() -> pd.DataFrame:
    """
    Load FERC operating expenses data.

    Only uses 'reported_value' rows to avoid double-counting with 
    calculated subtotals.

    Returns:
        DataFrame with operating expenses

    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path: Path = DATA_FERC / FERC_OPERATING_EXPENSES
    
    if not file_path.exists():
        raise FileNotFoundError(f"FERC file not found: {file_path}")
    
    df: pd.DataFrame = pd.read_parquet(file_path)
    
    # Filter to target utilities and years
    target_ferc_ids: List[int] = [mapping[0] for mapping in UTILITY_MAPPING.values()]
    
    # Filter to reported_value only to avoid double-counting with calculated subtotals
    filtered: pd.DataFrame = df[
        (df["utility_id_ferc1"].isin(target_ferc_ids)) &
        (df["report_year"].isin(YEARS)) &
        (df["row_type_xbrl"] == "reported_value")
    ].copy()
    
    return filtered


def load_ferc_utility_plant() -> pd.DataFrame:
    """
    Load FERC utility plant summary data and pivot to wide format.

    Extracts utility_plant_in_service and accumulated_provision_for_depreciation
    from the long format data.

    Returns:
        DataFrame with utility_id_ferc1, report_year, utility_plant_in_service,
        and accumulated_provision_for_depreciation columns

    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path: Path = DATA_FERC / FERC_UTILITY_PLANT
    
    if not file_path.exists():
        raise FileNotFoundError(f"FERC file not found: {file_path}")
    
    df: pd.DataFrame = pd.read_parquet(file_path)
    
    # Filter to target utilities, years, and electric type
    target_ferc_ids: List[int] = [mapping[0] for mapping in UTILITY_MAPPING.values()]
    
    filtered: pd.DataFrame = df[
        (df["utility_id_ferc1"].isin(target_ferc_ids)) &
        (df["report_year"].isin(YEARS)) &
        (df["utility_type"] == UTILITY_TYPE_ELECTRIC)
    ].copy()
    
    # Extract utility_plant_in_service
    # Use calculated_value for utility_plant_in_service_classified_and_unclassified
    ups_filter: pd.Series = (
        (filtered["utility_plant_asset_type"] == "utility_plant_in_service_classified_and_unclassified") &
        (filtered["row_type_xbrl"] == "calculated_value")
    )
    ups_data: pd.DataFrame = filtered[ups_filter][
        ["utility_id_ferc1", "report_year", "ending_balance"]
    ].copy()
    ups_data = ups_data.rename(columns={"ending_balance": "utility_plant_in_service"})
    
    # Extract accumulated_provision_for_depreciation
    # Use calculated_value for accumulated_provision_for_depreciation_amortization_and_depletion_of_plant_utility
    acc_filter: pd.Series = (
        (filtered["utility_plant_asset_type"] == "accumulated_provision_for_depreciation_amortization_and_depletion_of_plant_utility") &
        (filtered["row_type_xbrl"] == "calculated_value")
    )
    acc_data: pd.DataFrame = filtered[acc_filter][
        ["utility_id_ferc1", "report_year", "ending_balance"]
    ].copy()
    acc_data = acc_data.rename(columns={"ending_balance": "accumulated_provision_for_depreciation"})
    
    # Join the two datasets
    result: pd.DataFrame = ups_data.merge(
        acc_data,
        on=["utility_id_ferc1", "report_year"],
        how="outer"
    )
    
    return result


def load_ferc_income_statements() -> pd.DataFrame:
    """
    Load FERC income statements data.

    Returns:
        DataFrame with income statement data

    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path: Path = DATA_FERC / FERC_INCOME_STATEMENTS
    
    if not file_path.exists():
        raise FileNotFoundError(f"FERC file not found: {file_path}")
    
    df: pd.DataFrame = pd.read_parquet(file_path)
    
    # Filter to target utilities, years, and electric type
    target_ferc_ids: List[int] = [mapping[0] for mapping in UTILITY_MAPPING.values()]
    
    filtered: pd.DataFrame = df[
        (df["utility_id_ferc1"].isin(target_ferc_ids)) &
        (df["report_year"].isin(YEARS)) &
        (df["utility_type"] == UTILITY_TYPE_ELECTRIC)
    ].copy()
    
    return filtered


def load_ferc_operating_revenues() -> pd.DataFrame:
    """
    Load FERC operating revenues from income statement schedule 114.

    Extracts operating revenues (ferc_account == '400') for electric utilities.

    Returns:
        DataFrame with utility_id_ferc1, report_year, and operating_revenues columns

    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path: Path = DATA_FERC / FERC_INCOME_STATEMENTS
    
    if not file_path.exists():
        raise FileNotFoundError(f"FERC file not found: {file_path}")
    
    df: pd.DataFrame = pd.read_parquet(file_path)
    
    # Filter to target utilities, years, electric type, and account 400
    target_ferc_ids: List[int] = [mapping[0] for mapping in UTILITY_MAPPING.values()]
    
    filtered: pd.DataFrame = df[
        (df["utility_id_ferc1"].isin(target_ferc_ids)) &
        (df["report_year"].isin(YEARS)) &
        (df["utility_type"] == UTILITY_TYPE_ELECTRIC) &
        (df["ferc_account"] == "400")
    ].copy()
    
    # Select and rename columns
    result: pd.DataFrame = filtered[
        ["utility_id_ferc1", "report_year", "dollar_value"]
    ].copy()
    result = result.rename(columns={"dollar_value": "operating_revenues_ferc"})
    
    # Aggregate in case of multiple rows per utility-year
    result = result.groupby(
        ["utility_id_ferc1", "report_year"],
        as_index=False
    )["operating_revenues_ferc"].sum()
    
    return result


def load_ferc_utility_association() -> pd.DataFrame:
    """
    Load FERC utility association mapping.

    Returns:
        DataFrame with utility ID to name mapping

    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path: Path = DATA_FERC / FERC_UTILITY_ASSOCIATION
    
    if not file_path.exists():
        raise FileNotFoundError(f"FERC file not found: {file_path}")
    
    df: pd.DataFrame = pd.read_parquet(file_path)
    
    # Filter to target utilities
    target_ferc_ids: List[int] = [mapping[0] for mapping in UTILITY_MAPPING.values()]
    
    filtered: pd.DataFrame = df[
        df["utility_id_ferc1"].isin(target_ferc_ids)
    ].copy()
    
    return filtered

