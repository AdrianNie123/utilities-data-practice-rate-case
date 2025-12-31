"""Visualization module for Rate Case Analysis.

Generates professional charts suitable for regulatory staff reports.
All figures saved to outputs/figures/ at 300 dpi.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import DATA_PROCESSED, PROJECT_ROOT


# Output directory
FIGURES_DIR: Path = PROJECT_ROOT / "outputs" / "figures"

# Utility colors (consistent across all charts)
UTILITY_COLORS: Dict[str, str] = {
    "PG&E": "#1f77b4",
    "SCE": "#ff7f0e",
    "SDG&E": "#2ca02c",
}

# Standard source citation
SOURCE_CITATION: str = "Source: FERC Form 1, EIA-861 (2018-2023)"

# Chart settings
FIGSIZE_STANDARD: Tuple[int, int] = (10, 6)
DPI: int = 300


def setup_style() -> None:
    """Configure matplotlib style for professional charts."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 16,
        "figure.dpi": 100,
    })


def add_source_citation(ax: plt.Axes, y_offset: float = -0.12) -> None:
    """Add source citation to chart."""
    ax.annotate(
        SOURCE_CITATION,
        xy=(0, y_offset),
        xycoords="axes fraction",
        fontsize=8,
        color="gray",
        style="italic",
    )
    


def format_billions(value: float) -> str:
    """Format value as billions with one decimal."""
    return f"${value / 1e9:.1f}B"


def format_millions(value: float) -> str:
    """Format value as millions."""
    return f"${value / 1e6:.0f}M"


def load_analysis_ready() -> pd.DataFrame:
    """Load analysis-ready dataset."""
    return pd.read_parquet(DATA_PROCESSED / "analysis_ready.parquet")


def load_revenue_requirement() -> pd.DataFrame:
    """Load revenue requirement dataset."""
    return pd.read_parquet(DATA_PROCESSED / "revenue_requirement.parquet")


def load_bill_impact() -> pd.DataFrame:
    """Load bill impact dataset."""
    return pd.read_parquet(DATA_PROCESSED / "bill_impact.parquet")


def load_analysis_results() -> Dict:
    """Load analysis results JSON."""
    with open(DATA_PROCESSED / "analysis_results.json", "r") as f:
        return json.load(f)


def calculate_cagr(first_value: float, last_value: float, n_years: int) -> float:
    """Calculate compound annual growth rate."""
    if first_value <= 0 or n_years <= 0:
        return np.nan
    return ((last_value / first_value) ** (1.0 / n_years) - 1.0) * 100.0


def plot_om_trend(
    df: Optional[pd.DataFrame] = None,
    save: bool = True,
) -> plt.Figure:
    """
    Chart 1: O&M Trend by Utility (Line Chart).
    
    Shows O&M expense trends from 2018-2023 with CAGR annotations.
    """
    setup_style()
    
    if df is None:
        df = load_analysis_ready()
    
    fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)
    
    # Calculate CAGR for subtitle
    cagr_text_parts: List[str] = []
    
    for utility in ["PG&E", "SCE", "SDG&E"]:
        utility_data = df[df["utility_name"] == utility].sort_values("report_year")
        
        years = utility_data["report_year"].values
        om_values = utility_data["om_total"].values / 1e9  # Convert to billions
        
        # Plot line
        ax.plot(
            years,
            om_values,
            marker="o",
            markersize=8,
            linewidth=2.5,
            color=UTILITY_COLORS[utility],
            label=utility,
        )
        
        # Add direct labels on last point
        ax.annotate(
            utility,
            xy=(years[-1], om_values[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
            color=UTILITY_COLORS[utility],
            va="center",
        )
        
        # Calculate CAGR
        if len(om_values) >= 2:
            cagr = calculate_cagr(om_values[0], om_values[-1], len(years) - 1)
            cagr_text_parts.append(f"{utility}: {cagr:+.1f}%")
    
    # Title and subtitle
    ax.set_title("O&M Expense Trend (2018-2023)", fontsize=14, fontweight="bold", pad=20)
    subtitle = "CAGR: " + " | ".join(cagr_text_parts)
    ax.text(
        0.5, 1.02, subtitle,
        transform=ax.transAxes,
        fontsize=10,
        ha="center",
        color="gray",
    )
    
    # Axis labels
    ax.set_xlabel("Year")
    ax.set_ylabel("O&M Total ($ Billions)")
    ax.set_xticks(df["report_year"].unique())
    
    # Y-axis formatting
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:.0f}B"))
    
    # Expand x-axis to fit labels
    ax.set_xlim(2017.5, 2024)
    
    # Add source citation
    add_source_citation(ax)
    
    plt.tight_layout()
    
    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(FIGURES_DIR / "om_trend.png", dpi=DPI, bbox_inches="tight")
        print(f"Saved: {FIGURES_DIR / 'om_trend.png'}")
    
    return fig


def plot_peer_comparison(
    df: Optional[pd.DataFrame] = None,
    year: int = 2023,
    save: bool = True,
) -> plt.Figure:
    """
    Chart 2: Peer Comparison — Cost per Customer (Horizontal Bar).
    
    Shows O&M per customer for each utility with peer average comparison.
    """
    setup_style()
    
    if df is None:
        df = load_analysis_ready()
    
    # Filter to specified year
    data = df[df["report_year"] == year].copy()
    data = data.sort_values("om_per_customer", ascending=True)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Calculate peer average
    peer_avg = data["om_per_customer"].mean()
    
    # Plot horizontal bars
    utilities = data["utility_name"].tolist()
    values = data["om_per_customer"].tolist()
    colors = [UTILITY_COLORS[u] for u in utilities]
    
    bars = ax.barh(utilities, values, color=colors, height=0.6, edgecolor="white")
    
    # Add vertical line for peer average
    ax.axvline(peer_avg, color="red", linestyle="--", linewidth=2, label="Peer Average")
    ax.annotate(
        f"Peer Avg: ${peer_avg:,.0f}",
        xy=(peer_avg, len(utilities) - 0.5),
        xytext=(10, 0),
        textcoords="offset points",
        fontsize=9,
        color="red",
        va="center",
    )
    
    # Add value labels and percent difference
    for i, (utility, value) in enumerate(zip(utilities, values)):
        pct_diff = ((value - peer_avg) / peer_avg) * 100
        sign = "+" if pct_diff > 0 else ""
        
        # Value label
        ax.annotate(
            f"${value:,.0f}",
            xy=(value, i),
            xytext=(5, 0),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
            va="center",
        )
        
        # Percent difference
        ax.annotate(
            f"({sign}{pct_diff:.0f}%)",
            xy=(value, i),
            xytext=(70, 0),
            textcoords="offset points",
            fontsize=9,
            color="green" if pct_diff < 0 else "red",
            va="center",
        )
    
    # Find highest above average for subtitle
    max_util = data.loc[data["om_per_customer"].idxmax()]
    max_pct = ((max_util["om_per_customer"] - peer_avg) / peer_avg) * 100
    
    # Title and subtitle
    ax.set_title(f"O&M Cost per Customer ({year})", fontsize=14, fontweight="bold", pad=20)
    ax.text(
        0.5, 1.02,
        f"{max_util['utility_name']} spends {max_pct:.0f}% above peer average",
        transform=ax.transAxes,
        fontsize=10,
        ha="center",
        color="gray",
    )
    
    ax.set_xlabel("O&M per Customer ($)")
    ax.set_xlim(0, max(values) * 1.3)
    
    add_source_citation(ax)
    
    plt.tight_layout()
    
    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(FIGURES_DIR / "peer_comparison_cost_per_customer.png", dpi=DPI, bbox_inches="tight")
        print(f"Saved: {FIGURES_DIR / 'peer_comparison_cost_per_customer.png'}")
    
    return fig


def plot_rr_waterfall(
    df: Optional[pd.DataFrame] = None,
    utility: str = "PG&E",
    year: int = 2023,
    save: bool = True,
) -> plt.Figure:
    """
    Chart 3: Revenue Requirement Waterfall.
    
    Shows RR components building up to total.
    """
    setup_style()
    
    if df is None:
        df = load_revenue_requirement()
    
    # Filter to utility and year
    row = df[(df["utility_name"] == utility) & (df["report_year"] == year)].iloc[0]
    
    # Get RR components (use om_total minus om_other for O&M)
    om_expense = row["om_total"] - row.get("om_other", 0)
    depreciation = row["depreciation"]
    return_on_rb = row["return_on_rate_base"]
    taxes = row["taxes"]
    total_rr = row["revenue_requirement"]
    
    # Waterfall data
    categories = ["O&M\n(excl. pass-through)", "Depreciation", "Return on\nRate Base", "Taxes", "Revenue\nRequirement"]
    values = [om_expense, depreciation, return_on_rb, taxes, total_rr]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate waterfall positions
    cumulative = 0
    bars_data = []
    
    for i, (cat, val) in enumerate(zip(categories[:-1], values[:-1])):
        bars_data.append({
            "category": cat,
            "bottom": cumulative,
            "height": val,
            "color": "#4C72B0",  # Blue for additions
        })
        cumulative += val
    
    # Add total bar (starts from 0)
    bars_data.append({
        "category": categories[-1],
        "bottom": 0,
        "height": total_rr,
        "color": "#55A868",  # Green for total
    })
    
    # Plot bars
    x_positions = range(len(bars_data))
    
    for i, bar in enumerate(bars_data):
        ax.bar(
            i,
            bar["height"],
            bottom=bar["bottom"],
            color=bar["color"],
            edgecolor="white",
            linewidth=1.5,
            width=0.6,
        )
        
        # Add connecting lines between bars (except for last)
        if i < len(bars_data) - 2:
            next_bottom = bars_data[i + 1]["bottom"]
            ax.plot(
                [i + 0.3, i + 0.7],
                [bar["bottom"] + bar["height"], next_bottom + bars_data[i + 1]["height"]],
                color="gray",
                linestyle="--",
                linewidth=1,
                alpha=0.5,
            )
        
        # Value label
        label_y = bar["bottom"] + bar["height"] / 2
        ax.annotate(
            format_billions(bar["height"]),
            xy=(i, label_y),
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="white" if bar["height"] > 1e9 else "black",
        )
    
    # X-axis
    ax.set_xticks(x_positions)
    ax.set_xticklabels([b["category"] for b in bars_data], fontsize=10)
    
    # Y-axis
    ax.set_ylabel("$ Billions")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x/1e9:.0f}B"))
    
    # Title and subtitle
    ax.set_title(
        f"{utility} Revenue Requirement Components ({year})",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.text(
        0.5, 1.02,
        f"Total: {format_billions(total_rr)}",
        transform=ax.transAxes,
        fontsize=11,
        ha="center",
        color="gray",
    )
    
    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    add_source_citation(ax)
    
    plt.tight_layout()
    
    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"rr_waterfall_{utility.lower().replace('&', '').replace(' ', '_')}.png"
        fig.savefig(FIGURES_DIR / filename, dpi=DPI, bbox_inches="tight")
        print(f"Saved: {FIGURES_DIR / filename}")
    
    return fig


def plot_revenue_gap(
    df: Optional[pd.DataFrame] = None,
    year: int = 2023,
    save: bool = True,
) -> plt.Figure:
    """
    Chart 4: Revenue Gap by Utility (Bar Chart).
    
    Shows gap between calculated RR and actual revenue.
    """
    setup_style()
    
    if df is None:
        df = load_revenue_requirement()
    
    # Filter to year
    data = df[df["report_year"] == year].copy()
    data = data.sort_values("utility_name")
    
    fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)
    
    utilities = data["utility_name"].tolist()
    gaps = data["revenue_gap"].values / 1e9  # Convert to billions
    gap_pcts = data["revenue_gap_pct"].values
    
    # Colors: green for negative (over-collecting), red for positive (under-collecting)
    colors = ["#2ca02c" if g < 0 else "#d62728" for g in gaps]
    
    bars = ax.bar(utilities, gaps, color=colors, edgecolor="white", width=0.6)
    
    # Add percentage labels
    for i, (bar, pct) in enumerate(zip(bars, gap_pcts)):
        height = bar.get_height()
        sign = "+" if height > 0 else ""
        ax.annotate(
            f"{sign}{pct:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5 if height >= 0 else -15),
            textcoords="offset points",
            ha="center",
            fontsize=11,
            fontweight="bold",
        )
    
    # Add zero line
    ax.axhline(0, color="black", linewidth=0.8)
    
    # Title and subtitle
    ax.set_title(
        f"Revenue Gap: Calculated RR vs Actual Revenue ({year})",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.text(
        0.5, 1.02,
        "Negative = utility collecting more than calculated RR",
        transform=ax.transAxes,
        fontsize=10,
        ha="center",
        color="gray",
    )
    
    ax.set_ylabel("Revenue Gap ($ Billions)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:+.1f}B"))
    
    # Legend
    legend_elements = [
        mpatches.Patch(color="#2ca02c", label="Over-collecting (negative gap)"),
        mpatches.Patch(color="#d62728", label="Under-collecting (positive gap)"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", framealpha=0.9)
    
    add_source_citation(ax)
    
    plt.tight_layout()
    
    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(FIGURES_DIR / "revenue_gap.png", dpi=DPI, bbox_inches="tight")
        print(f"Saved: {FIGURES_DIR / 'revenue_gap.png'}")
    
    return fig


def plot_bill_impact(
    df: Optional[pd.DataFrame] = None,
    save: bool = True,
) -> plt.Figure:
    """
    Chart 5: Residential Bill Impact (Grouped Bar).
    
    Shows current vs proposed monthly bills.
    """
    setup_style()
    
    if df is None:
        df = load_bill_impact()
    
    df = df.sort_values("utility_name")
    
    fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)
    
    utilities = df["utility_name"].tolist()
    current_bills = df["current_monthly_bill"].tolist()
    proposed_bills = df["proposed_monthly_bill"].tolist()
    change_pcts = df["monthly_change_pct"].tolist()
    
    x = np.arange(len(utilities))
    width = 0.35
    
    # Plot bars
    bars1 = ax.bar(
        x - width / 2,
        current_bills,
        width,
        label="Current",
        color="#4C72B0",
        edgecolor="white",
    )
    bars2 = ax.bar(
        x + width / 2,
        proposed_bills,
        width,
        label="Proposed",
        color="#C44E52",
        edgecolor="white",
    )
    
    # Add value labels
    for bar in bars1:
        ax.annotate(
            f"${bar.get_height():.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
    
    for i, bar in enumerate(bars2):
        # Value label
        ax.annotate(
            f"${bar.get_height():.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
        # Percent change label
        ax.annotate(
            f"+{change_pcts[i]:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 18),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            fontweight="bold",
            color="#C44E52",
        )
    
    ax.set_xticks(x)
    ax.set_xticklabels(utilities)
    ax.set_ylabel("Monthly Bill ($)")
    
    # Title and subtitle
    ax.set_title(
        "Residential Bill Impact: Current vs Projected",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.text(
        0.5, 1.02,
        "Based on 500 kWh/month usage, 3% O&M escalation, 4% rate base growth",
        transform=ax.transAxes,
        fontsize=10,
        ha="center",
        color="gray",
    )
    
    ax.legend(loc="upper left")
    ax.set_ylim(0, max(proposed_bills) * 1.25)
    
    add_source_citation(ax)
    
    plt.tight_layout()
    
    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(FIGURES_DIR / "bill_impact.png", dpi=DPI, bbox_inches="tight")
        print(f"Saved: {FIGURES_DIR / 'bill_impact.png'}")
    
    return fig


def plot_yoy_heatmap(
    df: Optional[pd.DataFrame] = None,
    save: bool = True,
) -> plt.Figure:
    """
    Chart 6: Year-over-Year O&M Change Heatmap.
    
    Shows YoY percent change in O&M by utility and year.
    """
    setup_style()
    
    if df is None:
        df = load_analysis_ready()
    
    # Calculate YoY changes
    df = df.sort_values(["utility_name", "report_year"])
    df["om_yoy_pct"] = df.groupby("utility_name")["om_total"].pct_change() * 100
    
    # Pivot for heatmap (exclude first year since it has no prior year)
    pivot_data = df[df["report_year"] > 2018].pivot(
        index="utility_name",
        columns="report_year",
        values="om_yoy_pct",
    )
    
    # Reorder rows
    pivot_data = pivot_data.reindex(["PG&E", "SCE", "SDG&E"])
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Create heatmap
    cmap = sns.diverging_palette(130, 10, as_cmap=True)  # Green to Red
    
    sns.heatmap(
        pivot_data,
        annot=True,
        fmt=".1f",
        cmap=cmap,
        center=0,
        linewidths=2,
        linecolor="white",
        cbar_kws={"label": "YoY Change (%)"},
        ax=ax,
        annot_kws={"fontsize": 11, "fontweight": "bold"},
    )
    
    # Highlight outlier cells (>10% or <-5%)
    for i, utility in enumerate(pivot_data.index):
        for j, year in enumerate(pivot_data.columns):
            val = pivot_data.loc[utility, year]
            if not np.isnan(val) and (val > 10 or val < -5):
                ax.add_patch(plt.Rectangle(
                    (j, i), 1, 1,
                    fill=False,
                    edgecolor="black",
                    linewidth=3,
                ))
    
    # Title and subtitle
    ax.set_title(
        "Year-over-Year O&M Change (%)",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.text(
        0.5, 1.05,
        "Red indicates years with above-average cost growth | Black outline = outlier (>10% or <-5%)",
        transform=ax.transAxes,
        fontsize=10,
        ha="center",
        color="gray",
    )
    
    ax.set_xlabel("Year")
    ax.set_ylabel("")
    
    # Rotate x-axis labels
    plt.xticks(rotation=0)
    
    add_source_citation(ax, y_offset=-0.2)
    
    plt.tight_layout()
    
    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(FIGURES_DIR / "yoy_heatmap.png", dpi=DPI, bbox_inches="tight")
        print(f"Saved: {FIGURES_DIR / 'yoy_heatmap.png'}")
    
    return fig


def generate_all_figures() -> None:
    """
    Generate all visualization figures.
    
    Loads required data and creates all 6 charts, saving to outputs/figures/.
    """
    print("=" * 60)
    print("Generating Rate Case Analysis Figures")
    print("=" * 60)
    
    # Ensure output directory exists
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {FIGURES_DIR}\n")
    
    # Load data once
    print("Loading data...")
    df_analysis = load_analysis_ready()
    df_rr = load_revenue_requirement()
    df_bill = load_bill_impact()
    print(f"  - analysis_ready.parquet: {len(df_analysis)} rows")
    print(f"  - revenue_requirement.parquet: {len(df_rr)} rows")
    print(f"  - bill_impact.parquet: {len(df_bill)} rows")
    print()
    
    # Generate charts
    print("Generating charts...")
    
    print("\n1. O&M Trend Chart")
    plot_om_trend(df_analysis)
    
    print("\n2. Peer Comparison Chart")
    plot_peer_comparison(df_analysis)
    
    print("\n3. Revenue Requirement Waterfall (PG&E)")
    plot_rr_waterfall(df_rr, utility="PG&E")
    
    print("\n4. Revenue Gap Chart")
    plot_revenue_gap(df_rr)
    
    print("\n5. Bill Impact Chart")
    plot_bill_impact(df_bill)
    
    print("\n6. YoY Heatmap")
    plot_yoy_heatmap(df_analysis)
    
    print("\n" + "=" * 60)
    print("All figures generated successfully!")
    print("=" * 60)
    
    # Close all figures to free memory
    plt.close("all")


if __name__ == "__main__":
    generate_all_figures()

