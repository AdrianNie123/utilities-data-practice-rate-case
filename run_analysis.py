"""Script to run the complete analysis pipeline."""

import pandas as pd
from pathlib import Path

from src.config import DATA_PROCESSED
from src.analyze import run_analysis, print_key_findings, save_results


def main() -> None:
    """Run the analysis pipeline."""
    # Load data
    data_path: Path = DATA_PROCESSED / "analysis_ready.parquet"
    df: pd.DataFrame = pd.read_parquet(data_path)
    
    print(f"Loaded {len(df)} records from {data_path}")
    print(f"Utilities: {df['utility_name'].unique().tolist()}")
    print(f"Years: {sorted(df['report_year'].unique())}")
    
    # Run analysis
    print("\nRunning analysis...")
    results: dict = run_analysis(df)
    
    # Print key findings
    print_key_findings(results)
    
    # Save results
    output_path: Path = DATA_PROCESSED / "analysis_results.json"
    save_results(results, output_path)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()

