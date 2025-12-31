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
    forecast_test_year,
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
        - rr_dataset: Full dataset with RR calculations
        - test_year_forecast: Projected RR by utility
        - bill_impacts: Bill impact summary by utility
        - sensitivity: Sensitivity results for each utility
    """
    logger.info("Starting revenue requirement and bill impact analysis")

    results: Dict = {}

    # Apply revenue requirement calculations to full dataset
    logger.info("Calculating revenue requirements...")
    rr_dataset: pd.DataFrame = apply_rr_to_dataset(df)
    results["rr_dataset"] = rr_dataset
    logger.info(f"Revenue requirement calculated for {len(rr_dataset)} rows")

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

    print("\n1. REVENUE REQUIREMENT BY UTILITY (2023)")
    print("-" * 60)
    for _, row in rr_2023.iterrows():
        print(f"   {row['utility_name']:10s}: ${row['revenue_requirement']:,.0f}")

    # Revenue gap
    print("\n2. REVENUE GAP (Calculated RR vs Actual Revenue)")
    print("-" * 60)
    for _, row in rr_2023.iterrows():
        gap_sign: str = "+" if row["revenue_gap"] > 0 else ""
        print(
            f"   {row['utility_name']:10s}: {gap_sign}${row['revenue_gap']:,.0f} "
            f"({row['revenue_gap_pct']:+.1f}%)"
        )

    # Test year forecast
    print("\n3. PROJECTED RR CHANGE (2023 → 2024)")
    print("-" * 60)
    forecast: pd.DataFrame = results["test_year_forecast"]
    for _, row in forecast.iterrows():
        print(
            f"   {row['utility_name']:10s}: ${row['base_year_rr']:,.0f} → "
            f"${row['forecast_year_rr']:,.0f} ({row['rr_change_pct']:+.1f}%)"
        )

    # Bill impacts
    print("\n4. RESIDENTIAL BILL IMPACT")
    print("-" * 60)
    bill_impacts: pd.DataFrame = results["bill_impacts"]
    for _, row in bill_impacts.iterrows():
        print(
            f"   {row['utility_name']:10s}: ${row['current_monthly_bill']:.2f} → "
            f"${row['proposed_monthly_bill']:.2f} "
            f"({row['monthly_change_pct']:+.1f}%, ${row['annual_change_dollars']:+.2f}/yr)"
        )

    print("\n" + "=" * 80)
    print("Assumptions: Depreciation=3.5%, WACC=7.5%, Tax=27%, O&M escalation=3%, RB growth=4%")
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

