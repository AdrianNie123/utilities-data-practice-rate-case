"""Revenue requirement calculations for Rate Case Analysis.

ASSUMPTIONS (Industry Standards?):
- Depreciation rate: 3.5% of rate_base (typical utility asset life ~30 years)
- WACC (Weighted Average Cost of Capital): 7.5% (approximates CPUC-authorized returns)
- Tax rate: 27% (combined federal 21% + state 6%)

These assumptions are used because the actual values are not available in our datasets.
In a real rate case, these would be determined through regulatory proceedings.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

from src.config import DATA_PROCESSED


# Industry-standard assumptions
DEPRECIATION_RATE: float = 0.035  # 3.5% of rate base
WACC: float = 0.075  # 7.5% weighted average cost of capital
TAX_RATE: float = 0.27  # 27% combined federal + state tax rate


def calculate_revenue_requirement(
    row: pd.Series,
    depreciation_rate: float = DEPRECIATION_RATE,
    wacc: float = WACC,
    tax_rate: float = TAX_RATE,
    exclude_passthrough: bool = True,
) -> Dict[str, float]:
    """
    Calculate revenue requirement for a single utility-year.

    Revenue requirement components:
    - O&M expense: Direct operating costs (excludes pass-through costs by default)
    - Depreciation: Rate base × depreciation rate (3.5%)
    - Return on rate base: Rate base × WACC (7.5%)
    - Taxes: Gross-up for income taxes at 27%

    Note: Excludes 'om_other' which includes purchased power (account 555)
    and other pass-through costs that are recovered directly from customers.

    Arg:
        row: om_total, om_other, and rate_base values
        depreciation_rate: Annual depreciation as fraction of rate_base
        wacc: Weighted average cost of capital
        tax_rate: Combined tax rate
        exclude_passthrough: If True, exclude om_other (purchased power) from O&M

    Returns:
        Dictionary with all revenue requirement components

    Raises:
        ValueError: If required columns are missing or contain invalid data
    """
    # Validate required data
    if pd.isna(row.get("om_total")) or pd.isna(row.get("rate_base")):
        raise ValueError("Missing om_total or rate_base in row")

    om_total: float = float(row["om_total"])
    om_other: float = float(row.get("om_other", 0)) if not pd.isna(row.get("om_other")) else 0.0
    
    # Exclude pass-through costs (purchased power, etc.) if requested
    if exclude_passthrough:
        om_expense: float = om_total - om_other
    else:
        om_expense: float = om_total
        
    rate_base: float = float(row["rate_base"])

    # Handle negative or zero rate base
    if rate_base <= 0:
        depreciation: float = 0.0
        return_on_rate_base: float = 0.0
    else:
        depreciation: float = rate_base * depreciation_rate
        return_on_rate_base: float = rate_base * wacc

    # Calculate pre-tax total
    pre_tax_total: float = om_expense + depreciation + return_on_rate_base

    # Gross-up for taxes: taxes / (1 - tax_rate) gives pre-tax income needed
    # taxes = pre_tax_total * tax_rate / (1 - tax_rate)
    if tax_rate >= 1.0:
        raise ValueError(f"Invalid tax rate: {tax_rate}")

    taxes: float = pre_tax_total * tax_rate / (1.0 - tax_rate)

    # Total revenue requirement
    revenue_requirement: float = pre_tax_total + taxes

    return {
        "om_expense": om_expense,
        "om_passthrough": om_other if exclude_passthrough else 0.0,
        "depreciation": depreciation,
        "return_on_rate_base": return_on_rate_base,
        "pre_tax_total": pre_tax_total,
        "taxes": taxes,
        "revenue_requirement": revenue_requirement,
        "depreciation_rate": depreciation_rate,
        "wacc": wacc,
        "tax_rate": tax_rate,
        "exclude_passthrough": exclude_passthrough,
    }


def apply_rr_to_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply revenue requirement calculation to all rows.

    Adds columns:
    - depreciation: Rate base × 3.5%
    - return_on_rate_base: Rate base × 7.5%
    - taxes: Tax gross-up at 27%
    - revenue_requirement: Total RR
    - actual_revenue: From FERC operating_revenues_ferc (account 400)
    - revenue_gap: revenue_requirement - actual_revenue
    - revenue_gap_pct: (revenue_gap / actual_revenue) × 100

    Args:
        df: Analysis-ready DataFrame

    Returns:
        DataFrame with revenue requirement columns added

    Raises:
        ValueError: If required columns are missing
    """
    required_columns: list = ["om_total", "rate_base"]
    missing: list = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    result: pd.DataFrame = df.copy()

    # Calculate RR components for each row
    rr_components: list = []
    for idx, row in result.iterrows():
        try:
            rr: Dict[str, float] = calculate_revenue_requirement(row)
            rr_components.append(rr)
        except ValueError:
            # Skip rows with missing data
            rr_components.append({
                "om_expense": np.nan,
                "depreciation": np.nan,
                "return_on_rate_base": np.nan,
                "pre_tax_total": np.nan,
                "taxes": np.nan,
                "revenue_requirement": np.nan,
            })

    # Add RR columns
    rr_df: pd.DataFrame = pd.DataFrame(rr_components)
    result["depreciation"] = rr_df["depreciation"].values
    result["return_on_rate_base"] = rr_df["return_on_rate_base"].values
    result["taxes"] = rr_df["taxes"].values
    result["revenue_requirement"] = rr_df["revenue_requirement"].values

    # Use FERC operating revenues (account 400) if available, else fall back to EIA revenue
    if "operating_revenues_ferc" in result.columns:
        result["actual_revenue"] = result["operating_revenues_ferc"]
    else:
        result["actual_revenue"] = result["revenue_total_k"] * 1000.0

    result["revenue_gap"] = result["revenue_requirement"] - result["actual_revenue"]

    # Calculate percentage gap (handle division by zero)
    result["revenue_gap_pct"] = np.where(
        result["actual_revenue"] != 0,
        (result["revenue_gap"] / result["actual_revenue"]) * 100.0,
        np.nan,
    )

    return result


def forecast_test_year(
    df: pd.DataFrame,
    base_year: int = 2023,
    om_escalation: float = 0.03,
    rate_base_growth: float = 0.04,
    wacc: float = WACC,
) -> pd.DataFrame:
    """
    Project revenue requirement from base year using escalation factors.

    For each utility:
    - Gets base year values
    - Forecasts O&M with escalation (default 3%)
    - Forecasts rate base with growth (default 4%)
    - Recalculates revenue requirement

    Args:
        df: Analysis-ready DataFrame
        base_year: Base year for forecast (default 2023)
        om_escalation: Annual O&M cost escalation rate
        rate_base_growth: Annual rate base growth rate
        wacc: Weighted average cost of capital for forecast

    Returns:
        DataFrame with base and forecast revenue requirements by utility

    Raises:
        ValueError: If base year not found in data
    """
    base_data: pd.DataFrame = df[df["report_year"] == base_year].copy()

    if base_data.empty:
        raise ValueError(f"No data found for base year {base_year}")

    forecast_results: list = []

    for _, row in base_data.iterrows():
        utility_name: str = row["utility_name"]
        utility_id: int = int(row["utility_id_ferc1"])

        # Base year values
        base_om: float = float(row["om_total"])
        base_rate_base: float = float(row["rate_base"])

        # Skip if missing data
        if pd.isna(base_om) or pd.isna(base_rate_base):
            continue

        # Calculate base year RR
        base_rr_result: Dict[str, float] = calculate_revenue_requirement(row, wacc=wacc)
        base_year_rr: float = base_rr_result["revenue_requirement"]

        # Forecast values (one year out)
        forecast_om: float = base_om * (1.0 + om_escalation)
        forecast_rate_base: float = base_rate_base * (1.0 + rate_base_growth)

        # Create forecast row
        forecast_row: pd.Series = row.copy()
        forecast_row["om_total"] = forecast_om
        forecast_row["rate_base"] = forecast_rate_base

        # Calculate forecast RR
        forecast_rr_result: Dict[str, float] = calculate_revenue_requirement(
            forecast_row, wacc=wacc
        )
        forecast_year_rr: float = forecast_rr_result["revenue_requirement"]

        # Calculate change
        change: float = forecast_year_rr - base_year_rr
        change_pct: float = (change / base_year_rr) * 100.0 if base_year_rr != 0 else np.nan

        forecast_results.append({
            "utility_id_ferc1": utility_id,
            "utility_name": utility_name,
            "base_year": base_year,
            "forecast_year": base_year + 1,
            "base_om": base_om,
            "forecast_om": forecast_om,
            "base_rate_base": base_rate_base,
            "forecast_rate_base": forecast_rate_base,
            "base_year_rr": base_year_rr,
            "forecast_year_rr": forecast_year_rr,
            "rr_change": change,
            "rr_change_pct": change_pct,
            "om_escalation_rate": om_escalation,
            "rate_base_growth_rate": rate_base_growth,
            "wacc": wacc,
        })

    return pd.DataFrame(forecast_results)


def rr_sensitivity_by_wacc(
    utility_name: str,
    om_total: float,
    rate_base: float,
    wacc_range: Optional[list] = None,
) -> pd.DataFrame:
    """
    Calculate revenue requirement sensitivity to WACC changes.

    Tests revenue requirement under different WACC assumptions.

    Args:
        utility_name: Name of utility
        om_total: Total O&M expenses
        rate_base: Rate base value
        wacc_range: List of WACC values to test (default: 0.055 to 0.095)

    Returns:
        DataFrame with WACC sensitivity analysis
    """
    if wacc_range is None:
        wacc_range = [0.055, 0.065, 0.075, 0.085, 0.095]

    # Create mock row
    row: pd.Series = pd.Series({
        "om_total": om_total,
        "rate_base": rate_base,
    })

    results: list = []
    base_rr: Optional[float] = None

    for wacc in wacc_range:
        rr_result: Dict[str, float] = calculate_revenue_requirement(row, wacc=wacc)
        rr: float = rr_result["revenue_requirement"]

        if base_rr is None:
            base_rr = rr

        change_from_base: float = rr - base_rr
        change_pct: float = (change_from_base / base_rr) * 100.0 if base_rr != 0 else 0.0

        results.append({
            "utility_name": utility_name,
            "wacc": wacc,
            "wacc_pct": wacc * 100.0,
            "revenue_requirement": rr,
            "change_from_base": change_from_base,
            "change_pct": change_pct,
        })

    return pd.DataFrame(results)

