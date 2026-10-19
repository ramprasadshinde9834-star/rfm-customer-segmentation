"""
RFM Customer Segmentation - Online Retail dataset.

Usage:
    python src/rfm_analysis.py --data "data/Online Retail.xlsx"
    python src/rfm_analysis.py --data data/data.csv

Outputs:
    reports/rfm_customers.csv   one row per customer with R, F, M, scores, segment
    reports/segment_summary.csv summary table per segment
    images/*.png                charts
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # works without a display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")

SEGMENT_ORDER = [
    "Champions", "Loyal", "Potential Loyalists",
    "Need Attention", "At Risk", "Lost",
]


def load_data(path: str) -> pd.DataFrame:
    """Load the Excel (UCI) or CSV (Kaggle) version of the dataset."""
    if path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path, encoding="ISO-8859-1")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows that cannot be used for customer-level analysis."""
    df = df.dropna(subset=["CustomerID"])                        # unknown customers
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]    # cancellations
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]        # bad rows
    df = df.drop_duplicates().copy()
    df["CustomerID"] = df["CustomerID"].astype(int)
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
    return df


def build_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """One row per customer: Recency (days), Frequency (orders), Monetary (spend)."""
    snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("TotalPrice", "sum"),
    )
    return rfm


def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """Score each metric 1-5 using quintiles. For Recency, lower days = higher score."""
    rfm = rfm.copy()
    # rank(method="first") avoids duplicate bin edges in qcut
    rfm["R_Score"] = pd.qcut(rfm["Recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["RFM_Score"] = rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)
    return rfm


def assign_segment(row) -> str:
    """Rule-based segmentation using R and F scores. Order of rules matters."""
    r, f = row["R_Score"], row["F_Score"]
    if r >= 4 and f >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal"
    if r >= 4 and f <= 2:
        return "Potential Loyalists"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2:
        return "Lost"
    return "Need Attention"  # R = 3 and F <= 2


def summarize(rfm: pd.DataFrame) -> pd.DataFrame:
    summary = rfm.groupby("Segment").agg(
        Customers=("Recency", "size"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Avg_Monetary=("Monetary", "mean"),
        Total_Revenue=("Monetary", "sum"),
    )
    summary["Customer_Share_%"] = summary["Customers"] / summary["Customers"].sum() * 100
    summary["Revenue_Share_%"] = summary["Total_Revenue"] / summary["Total_Revenue"].sum() * 100
    summary = summary.reindex([s for s in SEGMENT_ORDER if s in summary.index])
    return summary.round(1)


def make_charts(rfm: pd.DataFrame, summary: pd.DataFrame, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    # 1. Segment size
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=summary.index, y=summary["Customers"], ax=ax, color="#4C72B0")
    ax.set_title("Number of Customers per Segment")
    ax.set_xlabel("")
    ax.set_ylabel("Customers")
    plt.xticks(rotation=30, ha="right")
    for i, v in enumerate(summary["Customers"]):
        ax.text(i, v, f"{int(v):,}", ha="center", va="bottom")
    plt.tight_layout()
    fig.savefig(outdir / "1_segment_size.png", dpi=150)
    plt.close(fig)

    # 2. Revenue share
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=summary.index, y=summary["Revenue_Share_%"], ax=ax, color="#55A868")
    ax.set_title("Revenue Share by Segment (%)")
    ax.set_xlabel("")
    ax.set_ylabel("% of total revenue")
    plt.xticks(rotation=30, ha="right")
    for i, v in enumerate(summary["Revenue_Share_%"]):
        ax.text(i, v, f"{v:.1f}%", ha="center", va="bottom")
    plt.tight_layout()
    fig.savefig(outdir / "2_revenue_share.png", dpi=150)
    plt.close(fig)

    # 3. R, F, M distributions (log scale for F and M because of skew)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    sns.histplot(rfm["Recency"], bins=30, ax=axes[0], color="#C44E52")
    axes[0].set_title("Recency (days since last order)")
    sns.histplot(np.log1p(rfm["Frequency"]), bins=30, ax=axes[1], color="#8172B2")
    axes[1].set_title("Frequency (log scale)")
    sns.histplot(np.log1p(rfm["Monetary"]), bins=30, ax=axes[2], color="#CCB974")
    axes[2].set_title("Monetary (log scale)")
    plt.tight_layout()
    fig.savefig(outdir / "3_rfm_distributions.png", dpi=150)
    plt.close(fig)

    # 4. Average R/F/M per segment (heatmap, each column normalised 0-1)
    avg = summary[["Avg_Recency", "Avg_Frequency", "Avg_Monetary"]]
    norm = (avg - avg.min()) / (avg.max() - avg.min())
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(norm, annot=avg, fmt=".1f", cmap="YlGnBu", cbar_kws={"label": "relative level"}, ax=ax)
    ax.set_title("Average R, F, M per Segment")
    ax.set_ylabel("")
    plt.tight_layout()
    fig.savefig(outdir / "4_segment_heatmap.png", dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="RFM customer segmentation")
    parser.add_argument("--data", required=True, help="Path to .xlsx or .csv file")
    parser.add_argument("--reports", default="reports", help="Folder for CSV outputs")
    parser.add_argument("--images", default="images", help="Folder for charts")
    args = parser.parse_args()

    raw = load_data(args.data)
    print(f"Raw data: {raw.shape[0]:,} rows")

    df = clean_data(raw)
    print(f"Clean data: {df.shape[0]:,} rows, {df['CustomerID'].nunique():,} customers")

    rfm = score_rfm(build_rfm(df))
    rfm["Segment"] = rfm.apply(assign_segment, axis=1)

    summary = summarize(rfm)
    print("\nSegment summary:\n", summary.to_string())

    reports = Path(args.reports)
    reports.mkdir(parents=True, exist_ok=True)
    rfm.to_csv(reports / "rfm_customers.csv")
    summary.to_csv(reports / "segment_summary.csv")
    make_charts(rfm, summary, Path(args.images))
    print(f"\nSaved CSVs to {reports}/ and charts to {args.images}/")


if __name__ == "__main__":
    main()
