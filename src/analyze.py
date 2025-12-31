"""Analysis functions for Rate Case Analysis."""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Union
from pathlib import Path

from scipy.stats import linregress
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import RegressionResults

from src.config import DATA_PROCESSED


def trend_analysis(df: pd.DataFrame, utility_id: int, metric: str) -> Dict[str, Union[float, str]]:
    """
    For a single utility and metric, calculate trend statistics.

    Calculates:
    - Linear regression slope and p-value
    - R-squared
    - CAGR (compound annual growth rate)
    - Mean, std, coefficient of variation

    Args:
        df: Analysis-ready DataFrame
        utility_id: FERC utility ID
        metric: Column name to analyze

    Returns:
        Dictionary with trend statistics

    Raises:
        ValueError: If utility_id or metric not found
    """
    # Filter to utility
    utility_data: pd.DataFrame = df[df["utility_id_ferc1"] == utility_id].copy()
    
    if utility_data.empty:
        raise ValueError(f"Utility ID {utility_id} not found in data")
    
    if metric not in utility_data.columns:
        raise ValueError(f"Metric {metric} not found in data")
    
    # Sort by year
    utility_data = utility_data.sort_values("report_year")
    
    # Extract values
    years: np.ndarray = utility_data["report_year"].values
    values: np.ndarray = utility_data[metric].values
    
    # Remove NaN values
    valid_mask: np.ndarray = ~np.isnan(values)
    years_clean: np.ndarray = years[valid_mask]
    values_clean: np.ndarray = values[valid_mask]
    
    if len(years_clean) < 2:
        raise ValueError(f"Insufficient data points for trend analysis: {len(years_clean)}")
    
    # Linear regression
    slope: float
    intercept: float
    r_value: float
    p_value: float
    std_err: float
    slope, intercept, r_value, p_value, std_err = linregress(years_clean, values_clean)
    
    r_squared: float = r_value ** 2
    
    # CAGR calculation
    first_value: float = values_clean[0]
    last_value: float = values_clean[-1]
    n_years: float = years_clean[-1] - years_clean[0]
    
    if first_value <= 0:
        cagr: float = np.nan
    else:
        cagr: float = ((last_value / first_value) ** (1.0 / n_years) - 1.0) * 100.0
    
    # Descriptive statistics
    mean_val: float = float(np.mean(values_clean))
    std_val: float = float(np.std(values_clean, ddof=1))
    cv: float = (std_val / mean_val * 100.0) if mean_val != 0 else np.nan
    
    return {
        "utility_id": int(utility_id),
        "metric": metric,
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "p_value": float(p_value),
        "cagr_percent": float(cagr),
        "mean": mean_val,
        "std": std_val,
        "coefficient_of_variation": float(cv),
        "n_years": int(n_years),
    }


def cost_driver_regression(df: pd.DataFrame) -> RegressionResults:
    """
    Regress om_total on cost drivers.

    Independent variables:
    - customers_total
    - sales_mwh_total
    - rate_base

    Args:
        df: Analysis-ready DataFrame

    Returns:
        Fitted OLS regression model

    Raises:
        ValueError: If required columns are missing
    """
    required_columns: List[str] = ["om_total", "customers_total", "sales_mwh_total", "rate_base"]
    missing_columns: List[str] = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Prepare data - remove rows with missing values
    clean_df: pd.DataFrame = df[required_columns].dropna()
    
    if len(clean_df) < 4:
        raise ValueError(f"Insufficient data points for regression: {len(clean_df)}")
    
    # Define dependent and independent variables
    y: pd.Series = clean_df["om_total"]
    X: pd.DataFrame = clean_df[["customers_total", "sales_mwh_total", "rate_base"]]
    
    # Add constant
    X_with_const: pd.DataFrame = sm.add_constant(X)
    
    # Fit OLS model
    model: RegressionResults = sm.OLS(y, X_with_const).fit()
    
    return model


def check_multicollinearity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for independent variables.

    Args:
        df: DataFrame with independent variables

    Returns:
        DataFrame with VIF values
    """
    X: pd.DataFrame = df[["customers_total", "sales_mwh_total", "rate_base"]].dropna()
    X_with_const: pd.DataFrame = sm.add_constant(X)
    
    vif_data: List[Dict[str, Union[str, float]]] = []
    
    for i in range(1, X_with_const.shape[1]):  # Skip constant
        vif: float = variance_inflation_factor(X_with_const.values, i)
        vif_data.append({
            "variable": X_with_const.columns[i],
            "vif": float(vif),
        })
    
    return pd.DataFrame(vif_data)


def detect_outliers(df: pd.DataFrame, metric: str, threshold: float = 2.0) -> pd.DataFrame:
    """
    Calculate z-scores for metric and flag outliers.

    Args:
        df: Analysis-ready DataFrame
        metric: Column name to analyze
        threshold: Z-score threshold (default 2.0)

    Returns:
        DataFrame with flagged outlier rows

    Raises:
        ValueError: If metric column not found
    """
    if metric not in df.columns:
        raise ValueError(f"Metric {metric} not found in data")
    
    df_copy: pd.DataFrame = df.copy()
    
    # Calculate z-scores
    values: pd.Series = df_copy[metric]
    mean_val: float = float(values.mean())
    std_val: float = float(values.std(ddof=1))
    
    if std_val == 0:
        df_copy["z_score"] = 0.0
        df_copy["is_outlier"] = False
    else:
        df_copy["z_score"] = (values - mean_val) / std_val
        df_copy["is_outlier"] = df_copy["z_score"].abs() > threshold
    
    # Return only flagged rows
    outliers: pd.DataFrame = df_copy[df_copy["is_outlier"]].copy()
    
    return outliers


def peer_benchmark(df: pd.DataFrame, year: int, metric: str) -> pd.DataFrame:
    """
    For a given year, rank utilities on metric.

    Calculates percentile and z-score for each utility.

    Args:
        df: Analysis-ready DataFrame
        year: Report year
        metric: Column name to rank

    Returns:
        DataFrame with rankings, percentiles, and z-scores

    Raises:
        ValueError: If year or metric not found
    """
    if metric not in df.columns:
        raise ValueError(f"Metric {metric} not found in data")
    
    # Filter to year
    year_data: pd.DataFrame = df[df["report_year"] == year].copy()
    
    if year_data.empty:
        raise ValueError(f"No data found for year {year}")
    
    # Calculate statistics
    values: pd.Series = year_data[metric].dropna()
    
    if values.empty:
        raise ValueError(f"No valid values for metric {metric} in year {year}")
    
    mean_val: float = float(values.mean())
    std_val: float = float(values.std(ddof=1))
    
    # Calculate z-scores and percentiles
    result: pd.DataFrame = year_data[["utility_id_ferc1", "utility_name", metric]].copy()
    
    if std_val == 0:
        result["z_score"] = 0.0
    else:
        result["z_score"] = (result[metric] - mean_val) / std_val
    
    # Calculate percentile rank (0-100)
    result["percentile"] = result[metric].rank(pct=True) * 100.0
    
    # Rank (1 = highest)
    result["rank"] = result[metric].rank(ascending=False, method="min").astype(int)
    
    # Sort by rank
    result = result.sort_values("rank")
    
    return result


def calculate_yoy_change(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """
    For each utility, calculate year-over-year percent change.

    Args:
        df: Analysis-ready DataFrame
        metric: Column name to analyze

    Returns:
        DataFrame with utility, year, metric_value, yoy_pct_change

    Raises:
        ValueError: If metric column not found
    """
    if metric not in df.columns:
        raise ValueError(f"Metric {metric} not found in data")
    
    df_copy: pd.DataFrame = df[["utility_id_ferc1", "utility_name", "report_year", metric]].copy()
    df_copy = df_copy.sort_values(["utility_id_ferc1", "report_year"])
    
    # Calculate year-over-year change
    df_copy["prev_value"] = df_copy.groupby("utility_id_ferc1")[metric].shift(1)
    df_copy["prev_year"] = df_copy.groupby("utility_id_ferc1")["report_year"].shift(1)
    
    # Calculate percent change
    mask: pd.Series = df_copy["prev_value"].notna() & (df_copy["prev_value"] != 0)
    df_copy.loc[mask, "yoy_pct_change"] = (
        (df_copy.loc[mask, metric] - df_copy.loc[mask, "prev_value"]) /
        df_copy.loc[mask, "prev_value"].abs() * 100.0
    )
    
    # Select and rename columns
    result: pd.DataFrame = df_copy[[
        "utility_id_ferc1",
        "utility_name",
        "report_year",
        metric,
        "yoy_pct_change",
    ]].copy()
    
    result = result.rename(columns={metric: "metric_value"})
    
    return result


def summary_by_utility(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by utility and calculate summary statistics.

    Calculates mean, std, min, max, CAGR for:
    - om_total
    - om_per_customer
    - om_per_mwh
    - rate_base

    Args:
        df: Analysis-ready DataFrame

    Returns:
        Summary statistics DataFrame
    """
    metrics: List[str] = ["om_total", "om_per_customer", "om_per_mwh", "rate_base"]
    available_metrics: List[str] = [m for m in metrics if m in df.columns]
    
    if not available_metrics:
        raise ValueError("No valid metrics found in data")
    
    summary_data: List[Dict[str, Union[int, str, float]]] = []
    
    for utility_id in df["utility_id_ferc1"].unique():
        utility_data: pd.DataFrame = df[df["utility_id_ferc1"] == utility_id].copy()
        utility_name: str = utility_data["utility_name"].iloc[0]
        utility_data = utility_data.sort_values("report_year")
        
        for metric in available_metrics:
            values: pd.Series = utility_data[metric].dropna()
            
            if len(values) < 2:
                continue
            
            mean_val: float = float(values.mean())
            std_val: float = float(values.std(ddof=1))
            min_val: float = float(values.min())
            max_val: float = float(values.max())
            
            # Calculate CAGR
            first_value: float = values.iloc[0]
            last_value: float = values.iloc[-1]
            n_years: float = float(utility_data["report_year"].iloc[-1] - utility_data["report_year"].iloc[0])
            
            if first_value > 0 and n_years > 0:
                cagr: float = ((last_value / first_value) ** (1.0 / n_years) - 1.0) * 100.0
            else:
                cagr = np.nan
            
            summary_data.append({
                "utility_id_ferc1": int(utility_id),
                "utility_name": utility_name,
                "metric": metric,
                "mean": mean_val,
                "std": std_val,
                "min": min_val,
                "max": max_val,
                "cagr_percent": float(cagr),
                "n_years": int(n_years),
            })
    
    return pd.DataFrame(summary_data)


def run_analysis(df: pd.DataFrame) -> Dict[str, Union[Dict, RegressionResults, pd.DataFrame, str]]:
    """
    Execute all analyses and return results.

    Args:
        df: Analysis-ready DataFrame

    Returns:
        Dictionary with all analysis results
    """
    results: Dict[str, Union[Dict, RegressionResults, pd.DataFrame, str]] = {}
    
    # 1. Trend analysis for each utility on om_total
    trend_results: Dict[str, Dict[str, Union[float, str]]] = {}
    utility_ids: List[int] = df["utility_id_ferc1"].unique().tolist()
    
    for utility_id in utility_ids:
        try:
            trend_result: Dict[str, Union[float, str]] = trend_analysis(df, utility_id, "om_total")
            utility_name: str = df[df["utility_id_ferc1"] == utility_id]["utility_name"].iloc[0]
            trend_results[utility_name] = trend_result
        except Exception as e:
            trend_results[f"utility_{utility_id}"] = {"error": str(e)}
    
    results["trend_results"] = trend_results
    
    # 2. Cost driver regression
    try:
        regression_model: RegressionResults = cost_driver_regression(df)
        results["regression_model"] = regression_model
        results["regression_summary"] = regression_model.summary().as_text()
        
        # Check multicollinearity
        vif_df: pd.DataFrame = check_multicollinearity(df)
        results["vif"] = vif_df.to_dict("records")
    except Exception as e:
        results["regression_error"] = str(e)
    
    # 3. Outlier detection on om_per_customer
    try:
        outliers: pd.DataFrame = detect_outliers(df, "om_per_customer", threshold=2.0)
        results["outliers"] = outliers.to_dict("records") if not outliers.empty else []
    except Exception as e:
        results["outliers_error"] = str(e)
    
    # 4. Peer benchmarking for latest year on om_per_customer
    try:
        latest_year: int = int(df["report_year"].max())
        benchmarks: pd.DataFrame = peer_benchmark(df, latest_year, "om_per_customer")
        results["benchmarks"] = benchmarks.to_dict("records")
    except Exception as e:
        results["benchmarks_error"] = str(e)
    
    # 5. Year-over-year changes for om_total
    try:
        yoy_changes: pd.DataFrame = calculate_yoy_change(df, "om_total")
        results["yoy_changes"] = yoy_changes.to_dict("records")
    except Exception as e:
        results["yoy_changes_error"] = str(e)
    
    # 6. Summary statistics by utility
    try:
        utility_summaries: pd.DataFrame = summary_by_utility(df)
        results["utility_summaries"] = utility_summaries.to_dict("records")
    except Exception as e:
        results["utility_summaries_error"] = str(e)
    
    return results


def print_key_findings(results: Dict[str, Union[Dict, RegressionResults, pd.DataFrame, str]]) -> None:
    """
    Print key findings from analysis results.

    Args:
        results: Results dictionary from run_analysis()
    """
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    
    # Highest om_per_customer
    if "benchmarks" in results and results["benchmarks"]:
        benchmarks: List[Dict] = results["benchmarks"]
        highest: Dict = max(benchmarks, key=lambda x: x.get("om_per_customer", 0))
        print(f"\n1. Highest O&M per Customer: {highest.get('utility_name')} "
              f"(${highest.get('om_per_customer', 0):,.2f})")
    
    # Fastest cost growth (CAGR)
    if "trend_results" in results:
        trend_results: Dict = results["trend_results"]
        cagr_data: List[tuple] = [
            (name, data.get("cagr_percent", np.nan))
            for name, data in trend_results.items()
            if isinstance(data, dict) and "cagr_percent" in data
        ]
        if cagr_data:
            fastest: tuple = max(cagr_data, key=lambda x: x[1] if not np.isnan(x[1]) else -np.inf)
            print(f"\n2. Fastest Cost Growth (CAGR): {fastest[0]} ({fastest[1]:.2f}%)")
    
    # Regression significance
    if "regression_model" in results:
        model: RegressionResults = results["regression_model"]
        pvalues: pd.Series = model.pvalues
        significant: List[str] = [
            var for var, pval in pvalues.items()
            if var != "const" and pval < 0.05
        ]
        print(f"\n3. Statistically Significant Cost Drivers (p < 0.05): {', '.join(significant) if significant else 'None'}")
        
        # VIF check
        if "vif" in results:
            vif_data: List[Dict] = results["vif"]
            high_vif: List[str] = [v["variable"] for v in vif_data if v.get("vif", 0) > 10]
            if high_vif:
                print(f"   Warning: High multicollinearity (VIF > 10) detected for: {', '.join(high_vif)}")
    
    # Outliers
    if "outliers" in results and results["outliers"]:
        outliers: List[Dict] = results["outliers"]
        print(f"\n4. Outlier Years Flagged: {len(outliers)}")
        for outlier in outliers[:5]:  # Show first 5
            print(f"   - {outlier.get('utility_name')} ({outlier.get('report_year')}): "
                  f"z-score = {outlier.get('z_score', 0):.2f}")
    else:
        print("\n4. Outlier Years Flagged: None")
    
    print("\n" + "=" * 80)


def save_results(results: Dict[str, Union[Dict, RegressionResults, pd.DataFrame, str]], output_path: Path) -> None:
    """
    Save analysis results to JSON file.

    Converts DataFrames and RegressionResults to serializable formats.

    Args:
        results: Results dictionary
        output_path: Path to save JSON file
    """
    # Create serializable copy
    serializable_results: Dict = {}
    
    for key, value in results.items():
        # Skip regression_model object (we keep regression_summary instead)
        if key == "regression_model":
            continue
        
        if isinstance(value, RegressionResults):
            # Skip any RegressionResults objects
            continue
        elif isinstance(value, pd.DataFrame):
            serializable_results[key] = value.to_dict("records")
        elif isinstance(value, dict):
            serializable_results[key] = value
        elif isinstance(value, str):
            serializable_results[key] = value
        elif isinstance(value, list):
            serializable_results[key] = value
        else:
            serializable_results[key] = str(value)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(output_path, "w") as f:
        json.dump(serializable_results, f, indent=2, default=str)
    
    with open('data/processed/analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    