"""Main ETL pipeline orchestration for Rate Case Analysis."""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict

from src.config import OUTPUT_FILE, DATA_PROCESSED
from src.extract import (
    extract_eia_data,
    filter_eia_to_ca_ious,
    aggregate_eia_duplicates,
    load_ferc_operating_expenses,
    load_ferc_utility_plant,
    load_ferc_income_statements,
    load_ferc_operating_revenues,
    load_ferc_utility_association,
)
from src.transform import (
    categorize_operating_expenses,
    pivot_expenses_to_wide,
    calculate_rate_base,
    join_ferc_eia_data,
    derive_metrics,
    select_final_columns,
    validate_output,
)
from src.revenue_requirement import (
    apply_rr_to_dataset,
    apply_grc_rr_to_dataset,
    forecast_test_year,
    print_grc_comparison,
)
from src.bill_impact import (
    bill_impact_analysis,
    run_all_bill_analyses,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger: logging.Logger = logging.getLogger(__name__)


def run_pipeline() -> pd.DataFrame:
    """
    Execute the complete ETL pipeline.

    Returns:
        Final analysis-ready DataFrame

    Raises:
        FileNotFoundError: If required input files are missing
        ValueError: If data validation fails
    """
    logger.info("Starting Rate Case Analysis pipeline")
    
    # Ensure output directory exists
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Extract
    logger.info("Step 1: Extracting data")
    
    logger.info("Loading EIA data...")
    eia_raw: pd.DataFrame = extract_eia_data()
    logger.info(f"Loaded {len(eia_raw)} EIA records")
    
    logger.info("Filtering EIA data to CA IOUs...")
    eia_filtered: pd.DataFrame = filter_eia_to_ca_ious(eia_raw)
    logger.info(f"Filtered to {len(eia_filtered)} CA IOU records")
    
    logger.info("Aggregating EIA duplicates...")
    eia_aggregated: pd.DataFrame = aggregate_eia_duplicates(eia_filtered)
    logger.info(f"Aggregated to {len(eia_aggregated)} unique utility-year records")
    
    logger.info("Loading FERC operating expenses...")
    ferc_expenses: pd.DataFrame = load_ferc_operating_expenses()
    logger.info(f"Loaded {len(ferc_expenses)} FERC expense records")
    
    logger.info("Loading FERC utility plant data...")
    ferc_plant: pd.DataFrame = load_ferc_utility_plant()
    logger.info(f"Loaded {len(ferc_plant)} FERC plant records")
    
    logger.info("Loading FERC income statements...")
    ferc_income: pd.DataFrame = load_ferc_income_statements()
    logger.info(f"Loaded {len(ferc_income)} FERC income records")
    
    logger.info("Loading FERC operating revenues (account 400)...")
    ferc_revenues: pd.DataFrame = load_ferc_operating_revenues()
    logger.info(f"Loaded {len(ferc_revenues)} FERC revenue records")
    
    logger.info("Loading FERC utility association...")
    ferc_assoc: pd.DataFrame = load_ferc_utility_association()
    logger.info(f"Loaded {len(ferc_assoc)} FERC association records")
    
    # Step 2: Transform
    logger.info("Step 2: Transforming data")
    
    logger.info("Categorizing FERC operating expenses...")
    ferc_expenses_categorized: pd.DataFrame = categorize_operating_expenses(ferc_expenses)
    
    logger.info("Pivoting expenses to wide format...")
    ferc_expenses_wide: pd.DataFrame = pivot_expenses_to_wide(ferc_expenses_categorized)
    logger.info(f"Pivoted to {len(ferc_expenses_wide)} utility-year records")
    
    logger.info("Calculating rate base...")
    ferc_plant_with_rate_base: pd.DataFrame = calculate_rate_base(ferc_plant)
    
    logger.info("Joining FERC and EIA data...")
    combined: pd.DataFrame = join_ferc_eia_data(
        ferc_expenses_wide,
        ferc_plant_with_rate_base,
        eia_aggregated,
        ferc_revenues
    )
    logger.info(f"Joined dataset has {len(combined)} records")
    
    # Step 3: Derive metrics
    logger.info("Step 3: Deriving metrics")
    with_metrics: pd.DataFrame = derive_metrics(combined)
    
    # Step 4: Select final columns
    logger.info("Step 4: Selecting final columns")
    final: pd.DataFrame = select_final_columns(with_metrics)
    
    # Validate output
    logger.info("Validating output...")
    validate_output(final)
    logger.info("Validation passed")
    
    # Step 5: Export
    logger.info(f"Step 5: Exporting to {OUTPUT_FILE}")
    final.to_parquet(OUTPUT_FILE, index=False, engine="pyarrow")
    logger.info(f"Pipeline complete. Output saved to {OUTPUT_FILE}")
    logger.info(f"Final dataset: {len(final)} rows, {len(final.columns)} columns")
    
    return final


def run_revenue_and_bill_analysis(df: pd.DataFrame) -> Dict:
    """
    Run all revenue requirement and bill impact analyses.

    Args:
        df: Analysis-ready DataFrame

    Returns:
        Dictionary with:
        - rr_dataset: Full dataset with RR calculations (both total and GRC)
        - test_year_forecast: Projected RR by utility
        - bill_impacts: Bill impact summary by utility
        - sensitivity: Sensitivity results for each utility
    """
    logger.info("Starting revenue requirement and bill impact analysis")

    results: Dict = {}

    # Apply TOTAL revenue requirement calculations
    logger.info("Calculating total utility revenue requirements...")
    rr_dataset: pd.DataFrame = apply_rr_to_dataset(df)
    logger.info(f"Total RR calculated for {len(rr_dataset)} rows")

    # Apply GRC-COMPARABLE revenue requirement calculations
    logger.info("Calculating GRC-comparable revenue requirements...")
    rr_dataset = apply_grc_rr_to_dataset(rr_dataset)
    results["rr_dataset"] = rr_dataset
    logger.info(f"GRC RR calculated for {len(rr_dataset)} rows")

    # Forecast test year
    logger.info("Forecasting test year revenue requirement...")
    test_year_forecast: pd.DataFrame = forecast_test_year(df, base_year=2023)
    results["test_year_forecast"] = test_year_forecast
    logger.info(f"Forecast generated for {len(test_year_forecast)} utilities")

    # Bill impact analysis
    logger.info("Running bill impact analysis...")
    bill_results: Dict = run_all_bill_analyses(df, base_year=2023)
    results["bill_impacts"] = bill_results["bill_impacts"]
    results["sensitivity"] = bill_results["sensitivity"]
    results["class_shares"] = bill_results["class_shares"]
    logger.info(f"Bill impact calculated for {len(results['bill_impacts'])} utilities")

    # Save outputs
    rr_output: Path = DATA_PROCESSED / "revenue_requirement.parquet"
    bill_output: Path = DATA_PROCESSED / "bill_impact.parquet"

    rr_dataset.to_parquet(rr_output, index=False, engine="pyarrow")
    logger.info(f"Revenue requirement saved to {rr_output}")

    results["bill_impacts"].to_parquet(bill_output, index=False, engine="pyarrow")
    logger.info(f"Bill impact saved to {bill_output}")

    return results


def print_analysis_summary(results: Dict) -> None:
    """
    Print summary of revenue requirement and bill impact analysis.

    Args:
        results: Dictionary from run_revenue_and_bill_analysis()
    """
    print("\n" + "=" * 80)
    print("REVENUE REQUIREMENT AND BILL IMPACT SUMMARY")
    print("=" * 80)

    # Revenue requirement by utility (2023)
    rr_dataset: pd.DataFrame = results["rr_dataset"]
    rr_2023: pd.DataFrame = rr_dataset[rr_dataset["report_year"] == 2023]

    print("\n1. UTILITY REVENUE REQUIREMENT (2023)")
    print("-" * 60)
    for _, row in rr_2023.iterrows():
        print(f"   {row['utility_name']:10s}: ${row['revenue_requirement'] / 1e9:,.2f}B")

    # GRC-Comparable Revenue Requirement
    print("\n2. GRC-COMPARABLE REVENUE REQUIREMENT (2023)")
    print("   (Dist + Cust Svc + A&G×70% + Depreciation + Return + 15% tax)")
    print("-" * 60)
    for _, row in rr_2023.iterrows():
        grc_rr: float = row.get("grc_revenue_requirement", 0)
        total_rr: float = row.get("revenue_requirement", 1)
        grc_share: float = (grc_rr / total_rr * 100) if total_rr > 0 else 0
        print(f"   {row['utility_name']:10s}: ${grc_rr / 1e9:,.2f}B ({grc_share:.0f}% of total)")

    # GRC O&M Breakdown
    print("\n3. GRC O&M BREAKDOWN (2023)")
    print("-" * 60)
    for _, row in rr_2023.iterrows():
        print(f"   {row['utility_name']:10s}:")
        print(f"      Distribution:     ${row['om_distribution'] / 1e9:,.2f}B")
        print(f"      Customer Service: ${row['om_customer_service'] / 1e9:,.2f}B")
        print(f"      A&G (70%):        ${row['om_admin_general'] * 0.70 / 1e9:,.2f}B")
        print(f"      GRC O&M Total:    ${row.get('grc_om', 0) / 1e9:,.2f}B")

    # Revenue gap
    print("\n4. REVENUE GAP (Total RR vs Actual Revenue)")
    print("-" * 60)
    for _, row in rr_2023.iterrows():
        gap_sign: str = "+" if row["revenue_gap"] > 0 else ""
        print(
            f"   {row['utility_name']:10s}: {gap_sign}${row['revenue_gap'] / 1e9:,.2f}B "
            f"({row['revenue_gap_pct']:+.1f}%)"
        )

    # Test year forecast
    print("\n5. PROJECTED RR CHANGE (2023 → 2024)")
    print("-" * 60)
    forecast: pd.DataFrame = results["test_year_forecast"]
    for _, row in forecast.iterrows():
        print(
            f"   {row['utility_name']:10s}: ${row['base_year_rr'] / 1e9:,.2f}B → "
            f"${row['forecast_year_rr'] / 1e9:,.2f}B ({row['rr_change_pct']:+.1f}%)"
        )

    # Bill impacts
    print("\n6. RESIDENTIAL BILL IMPACT")
    print("-" * 60)
    bill_impacts: pd.DataFrame = results["bill_impacts"]
    for _, row in bill_impacts.iterrows():
        print(
            f"   {row['utility_name']:10s}: ${row['current_monthly_bill']:.2f} → "
            f"${row['proposed_monthly_bill']:.2f} "
            f"({row['monthly_change_pct']:+.1f}%, ${row['annual_change_dollars']:+.2f}/yr)"
        )

    print("\n" + "=" * 80)
    print("METHODOLOGY NOTES:")
    print("  Total RR: All O&M + Depreciation + Return + 27% taxes")
    print("  GRC RR:   Dist + Cust Svc + (A&G × 70%) + Depreciation + Return + 15% taxes")
    print("  Excluded from GRC: Production (ERRA), Transmission (FERC), 30% A&G (gas)")
    print("=" * 80)


if __name__ == "__main__":
    try:
        result: pd.DataFrame = run_pipeline()
        print(f"\nPipeline completed successfully!")
        print(f"Output: {OUTPUT_FILE}")
        print(f"Records: {len(result)}")
        print(f"Columns: {len(result.columns)}")

        # Run revenue requirement and bill impact analysis
        print("\nRunning revenue requirement and bill impact analysis...")
        analysis_results: Dict = run_revenue_and_bill_analysis(result)
        print_analysis_summary(analysis_results)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

