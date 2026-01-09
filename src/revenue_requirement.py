"""Revenue requirement calculations for Rate Case Analysis.

TWO METHODOLOGIES:

1. TOTAL UTILITY REVENUE REQUIREMENT (calculate_revenue_requirement)
   - Includes all O&M costs
   - 27% tax gross-up
   - Useful for comparing to total operating revenues

2. GRC-COMPARABLE REVENUE REQUIREMENT (calculate_grc_revenue_requirement)
   - Only includes CPUC-regulated costs:
     * Distribution O&M
     * Customer Service O&M  
     * A&G × 70% (electric allocation)
   - Excludes:
     * Production costs (passed through via ERRA)
     * Transmission (FERC-regulated)
     * Fuel/purchased power (balancing account)
   - 15% simplified tax rate
   - Comparable to actual GRC filings (~3% variance expected from public data)

ASSUMPTIONS:
- Depreciation rate: 3.5% of rate_base (typical utility asset life ~30 years)
- WACC: 7.5% (approximates CPUC-authorized returns)
- Total tax rate: 27% (combined federal 21% + state 6%)
- GRC tax rate: 15% (simplified, excludes pass-through cost tax effects)
- A&G electric allocation: 70% (remainder is gas operations)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

from src.config import DATA_PROCESSED


# Industry-standard assumptions
DEPRECIATION_RATE: float = 0.035  # 3.5% of rate base
WACC: float = 0.075  # 7.5% weighted average cost of capital
TAX_RATE: float = 0.27  # 27% combined federal + state tax rate

# GRC-comparable assumptions
GRC_TAX_RATE: float = 0.15  # 15% simplified tax for GRC components
AG_ELECTRIC_ALLOCATION: float = 0.70  # 70% of A&G allocated to electric


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


def calculate_grc_revenue_requirement(
    row: pd.Series,
    depreciation_rate: float = DEPRECIATION_RATE,
    wacc: float = WACC,
    tax_rate: float = GRC_TAX_RATE,
    ag_allocation: float = AG_ELECTRIC_ALLOCATION,
) -> Dict[str, float]:
    """
    Calculate GRC-comparable revenue requirement for a single utility-year.

    GRC (General Rate Case) only covers CPUC-regulated costs:
    - Distribution O&M
    - Customer Service O&M
    - A&G × 70% (electric allocation)
    Revenue requirement formula:
        RR = O&M (GRC) + Depreciation + Return on Rate Base + Taxes
    EXCLUDES (not part of GRC):
    - Production O&M (recovered via ERRA balancing account)
    - Transmission O&M (FERC-regulated, not CPUC)
    - Purchased power (pass-through via balancing account)

    Args:
        row: DataFrame row with om_distribution, om_customer_service, 
             om_admin_general, and rate_base
        depreciation_rate: Annual depreciation as fraction of rate_base
        wacc: Weighted average cost of capital
        tax_rate: GRC tax rate (default 15%)
        ag_allocation: Fraction of A&G allocated to electric (default 70%)

    Returns:
        Dictionary with GRC revenue requirement components

    Raises:
        ValueError: If required columns are missing
    """
    # Validate required columns
    required_cols: list = ["om_distribution", "om_customer_service", "om_admin_general", "rate_base"]
    for col in required_cols:
        if col not in row.index or pd.isna(row.get(col)):
            raise ValueError(f"Missing or null value for: {col}")

    # Extract GRC-recoverable O&M components
    om_distribution: float = float(row["om_distribution"])
    om_customer_service: float = float(row["om_customer_service"])
    om_admin_general: float = float(row["om_admin_general"])
    rate_base: float = float(row["rate_base"])

    # Apply electric allocation to A&G (remainder is gas)
    om_ag_allocated: float = om_admin_general * ag_allocation

    # GRC-comparable O&M (excludes production, transmission)
    grc_om: float = om_distribution + om_customer_service + om_ag_allocated

    # Depreciation and return on rate base
    if rate_base <= 0:
        depreciation: float = 0.0
        return_on_rate_base: float = 0.0
    else:
        depreciation: float = rate_base * depreciation_rate
        return_on_rate_base: float = rate_base * wacc

    # Pre-tax total
    pre_tax_total: float = grc_om + depreciation + return_on_rate_base

    # Simplified tax calculation for GRC (15% of pre-tax)
    taxes: float = pre_tax_total * tax_rate

    # Total GRC revenue requirement
    grc_revenue_requirement: float = pre_tax_total + taxes

    return {
        "om_distribution": om_distribution,
        "om_customer_service": om_customer_service,
        "om_admin_general": om_admin_general,
        "om_ag_allocated": om_ag_allocated,
        "grc_om": grc_om,
        "depreciation": depreciation,
        "return_on_rate_base": return_on_rate_base,
        "pre_tax_total": pre_tax_total,
        "taxes": taxes,
        "grc_revenue_requirement": grc_revenue_requirement,
        "rate_base": rate_base,
        "depreciation_rate": depreciation_rate,
        "wacc": wacc,
        "tax_rate": tax_rate,
        "ag_allocation": ag_allocation,
    }


def apply_grc_rr_to_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply GRC-comparable revenue requirement calculation to all rows.

    Adds columns:
    - grc_om: Distribution + Customer Service + (A&G × 70%)
    - grc_depreciation: Rate base × 3.5%
    - grc_return_on_rate_base: Rate base × 7.5%
    - grc_taxes: Pre-tax total × 15%
    - grc_revenue_requirement: Total GRC RR

    Args:
        df: Analysis-ready DataFrame

    Returns:
        DataFrame with GRC revenue requirement columns added
    """
    required_columns: list = ["om_distribution", "om_customer_service", "om_admin_general", "rate_base"]
    missing: list = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for GRC calculation: {missing}")

    result: pd.DataFrame = df.copy()

    # Calculate GRC RR components for each row
    grc_components: list = []
    for idx, row in result.iterrows():
        try:
            grc: Dict[str, float] = calculate_grc_revenue_requirement(row)
            grc_components.append(grc)
        except ValueError:
            grc_components.append({
                "grc_om": np.nan,
                "om_ag_allocated": np.nan,
                "depreciation": np.nan,
                "return_on_rate_base": np.nan,
                "taxes": np.nan,
                "grc_revenue_requirement": np.nan,
            })

    # Add GRC columns
    grc_df: pd.DataFrame = pd.DataFrame(grc_components)
    result["grc_om"] = grc_df["grc_om"].values
    result["om_ag_allocated"] = grc_df["om_ag_allocated"].values
    result["grc_depreciation"] = grc_df["depreciation"].values
    result["grc_return_on_rate_base"] = grc_df["return_on_rate_base"].values
    result["grc_taxes"] = grc_df["taxes"].values
    result["grc_revenue_requirement"] = grc_df["grc_revenue_requirement"].values

    return result


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


def compare_rr_methodologies(df: pd.DataFrame, year: int = 2023) -> pd.DataFrame:
    """
    Compare total utility RR vs GRC-comparable RR for a given year.

    Shows what portion of utility costs are GRC-recoverable vs pass-through.

    Args:
        df: Analysis-ready DataFrame with both RR calculations applied
        year: Year to analyze (default 2023)

    Returns:
        DataFrame comparing methodologies by utility
    """
    year_data: pd.DataFrame = df[df["report_year"] == year].copy()

    if year_data.empty:
        raise ValueError(f"No data found for year {year}")

    comparison: list = []

    for _, row in year_data.iterrows():
        utility_name: str = row["utility_name"]

        # Total utility RR (if calculated)
        total_rr: float = float(row.get("revenue_requirement", np.nan))

        # GRC-comparable RR (if calculated)
        grc_rr: float = float(row.get("grc_revenue_requirement", np.nan))

        # Component breakdown
        om_production: float = float(row.get("om_production", 0))
        om_transmission: float = float(row.get("om_transmission", 0))
        om_distribution: float = float(row.get("om_distribution", 0))
        om_customer_service: float = float(row.get("om_customer_service", 0))
        om_admin_general: float = float(row.get("om_admin_general", 0))
        grc_om: float = float(row.get("grc_om", np.nan))

        # Calculate excluded costs
        excluded_om: float = om_production + om_transmission + (om_admin_general * 0.30)

        # GRC share of total
        grc_share: float = (grc_rr / total_rr * 100.0) if total_rr > 0 else np.nan

        comparison.append({
            "utility_name": utility_name,
            "year": year,
            "total_om": float(row.get("om_total", np.nan)),
            "grc_om": grc_om,
            "excluded_om": excluded_om,
            "om_production": om_production,
            "om_transmission": om_transmission,
            "om_distribution": om_distribution,
            "om_customer_service": om_customer_service,
            "om_ag_full": om_admin_general,
            "om_ag_allocated": om_admin_general * 0.70,
            "total_revenue_requirement": total_rr,
            "grc_revenue_requirement": grc_rr,
            "grc_share_of_total_pct": grc_share,
        })

    return pd.DataFrame(comparison)


def print_grc_comparison(df: pd.DataFrame, year: int = 2023) -> None:
    """
    Print formatted comparison of GRC-comparable vs total RR.

    Args:
        df: DataFrame with both RR calculations applied
        year: Year to display
    """
    comparison: pd.DataFrame = compare_rr_methodologies(df, year)

    print("\n" + "=" * 80)
    print(f"GRC-COMPARABLE vs TOTAL REVENUE REQUIREMENT ({year})")
    print("=" * 80)
    print("\nMethodology Differences:")
    print("  Total RR: All O&M + Depreciation + Return + 27% taxes")
    print("  GRC RR:   Dist + Cust Svc + (A&G × 70%) + Depreciation + Return + 15% taxes")
    print("  Excluded: Production (ERRA), Transmission (FERC), 30% A&G (gas)")
    print("\n" + "-" * 80)

    for _, row in comparison.iterrows():
        utility: str = row["utility_name"]
        total_rr: float = row["total_revenue_requirement"]
        grc_rr: float = row["grc_revenue_requirement"]
        grc_share: float = row["grc_share_of_total_pct"]

        print(f"\n{utility}:")
        print(f"  GRC O&M Components:")
        print(f"    Distribution:       ${row['om_distribution'] / 1e9:,.2f}B")
        print(f"    Customer Service:   ${row['om_customer_service'] / 1e9:,.2f}B")
        print(f"    A&G (70%):          ${row['om_ag_allocated'] / 1e9:,.2f}B")
        print(f"    ---")
        print(f"    GRC O&M Total:      ${row['grc_om'] / 1e9:,.2f}B")
        print(f"  Excluded from GRC:")
        print(f"    Production:         ${row['om_production'] / 1e9:,.2f}B")
        print(f"    Transmission:       ${row['om_transmission'] / 1e9:,.2f}B")
        print(f"    A&G (30% gas):      ${row['om_ag_full'] * 0.30 / 1e9:,.2f}B")
        print(f"  Revenue Requirements:")
        print(f"    Total Utility RR:   ${total_rr / 1e9:,.2f}B")
        print(f"    GRC-Comparable RR:  ${grc_rr / 1e9:,.2f}B")
        print(f"    GRC Share of Total: {grc_share:.1f}%")

    print("\n" + "=" * 80)

