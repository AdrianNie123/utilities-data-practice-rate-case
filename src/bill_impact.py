"""Bill impact analysis for Rate Case Analysis.

ASSUMPTIONS:
- Average monthly residential consumption: 500 kWh (CA average)
- Customer class revenue shares derived from actual EIA-861 data
- Bill calculations assume uniform rate across usage levels (simplified)

These assumptions enable bill impact estimates without detailed rate schedules.
In practice, residential rates include tiered pricing and fixed charges.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.config import DATA_PROCESSED
from src.revenue_requirement import (
    calculate_revenue_requirement,
    DEPRECIATION_RATE,
    WACC,
    TAX_RATE,
)


# Default average monthly residential usage (kWh) - CA average
DEFAULT_AVG_MONTHLY_KWH: float = 500.0


def calculate_class_shares(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate actual revenue share by customer class from data.

    Revenue shares reflect actual contribution of each customer class
    to total utility revenues.

    Args:
        df: Analysis-ready DataFrame with revenue columns

    Returns:
        DataFrame with revenue shares by utility-year

    Raises:
        ValueError: If required columns are missing
    """
    required_columns: list = [
        "utility_id_ferc1",
        "utility_name",
        "report_year",
        "revenue_residential_k",
        "revenue_commercial_k",
        "revenue_industrial_k",
        "revenue_total_k",
    ]

    missing: list = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    result: pd.DataFrame = df[required_columns].copy()

    # Calculate shares (handle division by zero)
    for sector in ["residential", "commercial", "industrial"]:
        col_name: str = f"revenue_{sector}_k"
        share_name: str = f"{sector}_share"

        result[share_name] = np.where(
            result["revenue_total_k"] != 0,
            result[col_name] / result["revenue_total_k"],
            np.nan,
        )

    return result


def calculate_residential_bill(
    revenue_requirement: float,
    residential_share: float,
    residential_sales_mwh: float,
    avg_monthly_kwh: float = DEFAULT_AVG_MONTHLY_KWH,
) -> Dict[str, float]:
    """
    Calculate average residential monthly bill.

    Allocates portion of revenue requirement to residential class
    and calculates average rate and monthly bill.

    Args:
        revenue_requirement: Total utility revenue requirement ($)
        residential_share: Fraction of revenue from residential class
        residential_sales_mwh: Total residential MWh sales
        avg_monthly_kwh: Average monthly consumption (default 500 kWh)

    Returns:
        Dictionary with residential_rr, avg_rate_per_kwh, monthly_bill

    Raises:
        ValueError: If inputs are invalid
    """
    if residential_sales_mwh <= 0:
        raise ValueError("Residential sales must be positive")

    if residential_share < 0 or residential_share > 1:
        raise ValueError(f"Invalid residential share: {residential_share}")

    # Allocate RR to residential class
    residential_rr: float = revenue_requirement * residential_share

    # Convert MWh to kWh for rate calculation
    residential_sales_kwh: float = residential_sales_mwh * 1000.0

    # Calculate average rate ($/kWh)
    avg_rate_per_kwh: float = residential_rr / residential_sales_kwh

    # Calculate monthly bill
    monthly_bill: float = avg_rate_per_kwh * avg_monthly_kwh

    return {
        "residential_rr": residential_rr,
        "residential_sales_kwh": residential_sales_kwh,
        "avg_rate_per_kwh": avg_rate_per_kwh,
        "monthly_bill": monthly_bill,
        "avg_monthly_kwh": avg_monthly_kwh,
    }


def bill_impact_analysis(
    df: pd.DataFrame,
    base_year: int = 2023,
    om_escalation: float = 0.03,
    rate_base_growth: float = 0.04,
    avg_monthly_kwh: float = DEFAULT_AVG_MONTHLY_KWH,
) -> pd.DataFrame:
    """
    For each utility, compare current to forecast bill.

    Steps:
    1. Calculate class shares from actual base year data
    2. Calculate current bill using base year revenue requirement
    3. Calculate proposed bill using forecast revenue requirement
    4. Compute change in dollars and percent

    Args:
        df: Analysis-ready DataFrame
        base_year: Year to use as baseline (default 2023)
        om_escalation: O&M cost escalation rate (default 3%)
        rate_base_growth: Rate base growth rate (default 4%)
        avg_monthly_kwh: Average monthly residential consumption

    Returns:
        DataFrame with bill impact by utility

    Raises:
        ValueError: If required columns missing or base year not found
    """
    required_columns: list = [
        "utility_id_ferc1",
        "utility_name",
        "report_year",
        "om_total",
        "rate_base",
        "revenue_residential_k",
        "revenue_total_k",
        "sales_mwh_residential",
    ]

    missing: list = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Filter to base year
    base_data: pd.DataFrame = df[df["report_year"] == base_year].copy()

    if base_data.empty:
        raise ValueError(f"No data found for base year {base_year}")

    results: list = []

    for _, row in base_data.iterrows():
        utility_name: str = row["utility_name"]
        utility_id: int = int(row["utility_id_ferc1"])

        # Get base values
        om_total: float = float(row["om_total"])
        rate_base: float = float(row["rate_base"])
        revenue_residential_k: float = float(row["revenue_residential_k"])
        revenue_total_k: float = float(row["revenue_total_k"])
        sales_mwh_residential: float = float(row["sales_mwh_residential"])

        # Skip if missing critical data
        if any(pd.isna([om_total, rate_base, sales_mwh_residential])):
            continue

        if sales_mwh_residential <= 0:
            continue

        # Calculate residential share from actual data
        if revenue_total_k != 0:
            residential_share: float = revenue_residential_k / revenue_total_k
        else:
            residential_share = 0.0

        # Calculate current (base year) revenue requirement
        current_rr_result: Dict[str, float] = calculate_revenue_requirement(row)
        current_rr: float = current_rr_result["revenue_requirement"]

        current_rate_per_kwh: float = (
            revenue_residential_k * 1000.0
        ) / (sales_mwh_residential * 1000.0)
        current_monthly_bill: float = current_rate_per_kwh * avg_monthly_kwh
        current_rate: float = current_rate_per_kwh

        # Forecast values
        forecast_om: float = om_total * (1.0 + om_escalation)
        forecast_rate_base: float = rate_base * (1.0 + rate_base_growth)

        # Create forecast row
        forecast_row: pd.Series = row.copy()
        forecast_row["om_total"] = forecast_om
        forecast_row["rate_base"] = forecast_rate_base

        # Calculate forecast revenue requirement
        forecast_rr_result: Dict[str, float] = calculate_revenue_requirement(forecast_row)
        forecast_rr: float = forecast_rr_result["revenue_requirement"]

        if current_rr == 0:
            continue

        change_factor: float = forecast_rr / current_rr
        proposed_monthly_bill: float = current_monthly_bill * change_factor
        proposed_rate: float = current_rate * change_factor

        # Calculate changes
        monthly_change_dollars: float = proposed_monthly_bill - current_monthly_bill
        monthly_change_pct: float = (
            (monthly_change_dollars / current_monthly_bill) * 100.0
            if current_monthly_bill != 0
            else 0.0
        )
        annual_change_dollars: float = monthly_change_dollars * 12.0

        results.append({
            "utility_id_ferc1": utility_id,
            "utility_name": utility_name,
            "base_year": base_year,
            "residential_share": residential_share,
            "residential_share_pct": residential_share * 100.0,
            "current_rr": current_rr,
            "proposed_rr": forecast_rr,
            "current_rate_per_kwh": current_rate,
            "proposed_rate_per_kwh": proposed_rate,
            "current_monthly_bill": current_monthly_bill,
            "proposed_monthly_bill": proposed_monthly_bill,
            "monthly_change_dollars": monthly_change_dollars,
            "monthly_change_pct": monthly_change_pct,
            "annual_change_dollars": annual_change_dollars,
            "avg_monthly_kwh": avg_monthly_kwh,
            "om_escalation": om_escalation,
            "rate_base_growth": rate_base_growth,
        })

    return pd.DataFrame(results)


def sensitivity_analysis(
    utility_name: str,
    base_om: float,
    base_rate_base: float,
    residential_share: float,
    residential_sales_mwh: float,
    avg_monthly_kwh: float = DEFAULT_AVG_MONTHLY_KWH,
) -> pd.DataFrame:
    """
    Test bill impact under different assumptions.

    Scenarios (vary one assumption at a time):
    - Base case: 3% O&M escalation, 4% rate base growth, 7.5% WACC
    - High O&M: 5% O&M escalation
    - Low O&M: 1% O&M escalation
    - High rate base: 6% rate base growth
    - Low rate base: 2% rate base growth
    - High WACC: 8.5%
    - Low WACC: 6.5%

    Args:
        utility_name: Name of utility
        base_om: Base year O&M expenses
        base_rate_base: Base year rate base
        residential_share: Fraction of revenue from residential
        residential_sales_mwh: Total residential MWh sales
        avg_monthly_kwh: Average monthly consumption

    Returns:
        DataFrame with scenario analysis results
    """
    # Define scenarios
    scenarios: List[Dict] = [
        {"name": "Base Case", "om_esc": 0.03, "rb_growth": 0.04, "wacc": 0.075},
        {"name": "High O&M Escalation", "om_esc": 0.05, "rb_growth": 0.04, "wacc": 0.075},
        {"name": "Low O&M Escalation", "om_esc": 0.01, "rb_growth": 0.04, "wacc": 0.075},
        {"name": "High Rate Base Growth", "om_esc": 0.03, "rb_growth": 0.06, "wacc": 0.075},
        {"name": "Low Rate Base Growth", "om_esc": 0.03, "rb_growth": 0.02, "wacc": 0.075},
        {"name": "High WACC", "om_esc": 0.03, "rb_growth": 0.04, "wacc": 0.085},
        {"name": "Low WACC", "om_esc": 0.03, "rb_growth": 0.04, "wacc": 0.065},
    ]

    results: list = []
    base_case_bill: Optional[float] = None

    for scenario in scenarios:
        # Forecast values
        forecast_om: float = base_om * (1.0 + scenario["om_esc"])
        forecast_rate_base: float = base_rate_base * (1.0 + scenario["rb_growth"])

        # Create mock row for RR calculation
        row: pd.Series = pd.Series({
            "om_total": forecast_om,
            "rate_base": forecast_rate_base,
        })

        # Calculate revenue requirement
        rr_result: Dict[str, float] = calculate_revenue_requirement(
            row, wacc=scenario["wacc"]
        )
        revenue_requirement: float = rr_result["revenue_requirement"]

        # Calculate bill
        try:
            bill_result: Dict[str, float] = calculate_residential_bill(
                revenue_requirement,
                residential_share,
                residential_sales_mwh,
                avg_monthly_kwh,
            )
            monthly_bill: float = bill_result["monthly_bill"]
        except ValueError:
            monthly_bill = np.nan

        # Track base case for comparison
        if base_case_bill is None:
            base_case_bill = monthly_bill

        # Calculate change from base case
        if base_case_bill is not None and not np.isnan(monthly_bill):
            change_from_base: float = monthly_bill - base_case_bill
            change_pct: float = (
                (change_from_base / base_case_bill) * 100.0
                if base_case_bill != 0
                else 0.0
            )
        else:
            change_from_base = np.nan
            change_pct = np.nan

        results.append({
            "utility_name": utility_name,
            "scenario": scenario["name"],
            "om_escalation": scenario["om_esc"],
            "rate_base_growth": scenario["rb_growth"],
            "wacc": scenario["wacc"],
            "revenue_requirement": revenue_requirement,
            "monthly_bill": monthly_bill,
            "change_from_base": change_from_base,
            "change_pct": change_pct,
        })

    return pd.DataFrame(results)


def run_all_bill_analyses(df: pd.DataFrame, base_year: int = 2023) -> Dict:
    """
    Run all bill impact analyses.

    Args:
        df: Analysis-ready DataFrame
        base_year: Year for baseline

    Returns:
        Dictionary with all analysis results
    """
    results: Dict = {}

    # Calculate class shares
    results["class_shares"] = calculate_class_shares(df)

    # Bill impact analysis
    results["bill_impacts"] = bill_impact_analysis(df, base_year=base_year)

    # Sensitivity analysis for each utility
    sensitivity_results: list = []
    base_data: pd.DataFrame = df[df["report_year"] == base_year].copy()

    for _, row in base_data.iterrows():
        utility_name: str = row["utility_name"]
        base_om: float = float(row["om_total"])
        base_rate_base: float = float(row["rate_base"])
        sales_mwh_residential: float = float(row["sales_mwh_residential"])
        revenue_residential_k: float = float(row["revenue_residential_k"])
        revenue_total_k: float = float(row["revenue_total_k"])

        if any(pd.isna([base_om, base_rate_base, sales_mwh_residential])):
            continue

        if sales_mwh_residential <= 0:
            continue

        residential_share: float = (
            revenue_residential_k / revenue_total_k
            if revenue_total_k != 0
            else 0.0
        )

        sensitivity_df: pd.DataFrame = sensitivity_analysis(
            utility_name,
            base_om,
            base_rate_base,
            residential_share,
            sales_mwh_residential,
        )
        sensitivity_results.append(sensitivity_df)

    if sensitivity_results:
        results["sensitivity"] = pd.concat(sensitivity_results, ignore_index=True)
    else:
        results["sensitivity"] = pd.DataFrame()

    return results

