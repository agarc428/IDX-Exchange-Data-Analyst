"""
Ariana Garcia Villabla
IDX

Week 2 Deliverables
------------------------------------
Objective: Fetch the FRED MORTGAGE30US series, resample it 
from weekly to monthly frequency, and merge it onto both 
combined datasets using a year-month key derived from 
transaction dates.
"""

import glob
import os
import re

import matplotlib
matplotlib.use("Agg")               
import matplotlib.pyplot as plt
import pandas as pd

pd.set_option("display.width", 160)
pd.set_option("display.max_rows", 300)

# Configuration
SOLD_DIR = "C:/Users/Arri7/OneDrive/Desktop/IDX_DA61/csv/CRML_Sold"
LISTED_DIR = "C:/Users/Arri7/OneDrive/Desktop/IDX_DA61/csv/CRML_Listed"
OUTPUT_DIR = "Week 2 Deliverables"
REPORT_DIR = os.path.join(OUTPUT_DIR, "reports")
FIG_DIR = os.path.join(OUTPUT_DIR, "figures")

#Fields for Analysis

MISSING_THRESHOLD = 90.0            

CORE_FIELDS = [
    "ListingKey", "ListingId", "PropertyType", "PropertySubType",
    "ClosePrice", "ListPrice", "OriginalListPrice",
    "LivingArea", "LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger",
    "DaysOnMarket", "YearBuilt",
    "CloseDate", "ListingContractDate", "PurchaseContractDate",
    "CountyOrParish", "City", "PostalCode", "Latitude", "Longitude",
    "MlsStatus", "SourceMonth",
]

NUMERIC_FIELDS = [
    "ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
    "LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger",
    "DaysOnMarket", "YearBuilt",
]

SUMMARY_FIELDS = ["ClosePrice", "LivingArea", "DaysOnMarket"]

METADATA_KEYWORDS = [
    "Key", "Id", "ID", "Timestamp", "Modification", "Agent", "Office",
    "Photo", "Media", "Originating", "Source", "Syndicat", "Internet",
    "Remarks", "Showing", "Contact", "Phone", "Email", "Url", "URL",
]

PERCENTILES = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

# Loading (same file discovery as Week 1, without the Residential filter)
def load_folder(folder, prefix):
    pattern = re.compile(rf"^{prefix}(\d{{6}})\.csv$")
    files = sorted(
        (m.group(1), p)
        for p in glob.glob(os.path.join(folder, f"{prefix}*.csv"))
        if (m := pattern.match(os.path.basename(p)))
    )
    if not files:
        raise FileNotFoundError(f"No {prefix}YYYYMM.csv files in {folder}")

    frames = []
    for ym, path in files:
        df = pd.read_csv(path, low_memory=False)
        df["SourceMonth"] = ym
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    print(f"{prefix}: {len(files)} files ({files[0][0]}–{files[-1][0]}), "
          f"{len(combined):,} rows")
    return combined

# 1. Dataset understanding
def describe_structure(df, label):
    section(f"{label}: STRUCTURE")
    rows, cols = df.shape
    print(f"Rows: {rows:,}   Columns: {cols}")

    print("\nColumn data types (count by dtype):")
    print(df.dtypes.astype(str).value_counts().to_string())

    print("\nFirst 3 rows (first 12 columns):")
    print(df.iloc[:3, :12].to_string())

    # Split columns into market-analysis fields vs metadata
    metadata = [c for c in df.columns
                if any(k in c for k in METADATA_KEYWORDS) and c not in CORE_FIELDS]
    market = [c for c in df.columns if c not in metadata]
    print(f"\nMarket analysis fields ({len(market)}):")
    print(", ".join(market))
    print(f"\nMetadata fields ({len(metadata)}):")
    print(", ".join(metadata))
    return market, metadata

# 2. Property types and the Residential filter
def property_types_and_filter(df, label):
    section(f"{label}: PROPERTY TYPES")
    counts = df["PropertyType"].value_counts(dropna=False)
    share = (counts / len(df) * 100).round(2)
    table = pd.DataFrame({"count": counts, "pct": share})
    print("Unique property types found:")
    print(table.to_string())

    res_pct = share.get("Residential", 0.0)
    print(f"\nResidential share: {res_pct:.2f}%  |  All other types: {100 - res_pct:.2f}%")

    # Drops except where PropertyType is exactly 'Residential'.
    before = len(df)
    filtered = df[df["PropertyType"] == "Residential"].copy()
    print(f"\nFilter applied: PropertyType == 'Residential'")
    print(f"Rows before: {before:,}   after: {len(filtered):,}   "
          f"removed: {before - len(filtered):,}")
    return filtered


# 3. Missing value analysis
def missing_value_report(df, label):
    section(f"{label}: MISSING VALUES (Residential only)")
    null_count = df.isnull().sum()
    null_pct = (null_count / len(df) * 100).round(2)
    report = pd.DataFrame({
        "null_count": null_count,
        "null_pct": null_pct,
        "dtype": df.dtypes.astype(str),
    }).sort_values("null_pct", ascending=False)
    report["over_90pct"] = report["null_pct"] > MISSING_THRESHOLD
    report["core_field"] = report.index.isin(CORE_FIELDS)

    # Drops except where the column is a core field
    report["decision"] = "keep"
    report.loc[report["over_90pct"] & ~report["core_field"], "decision"] = "drop"
    report.loc[report["over_90pct"] & report["core_field"], "decision"] = "keep (core)"

    print("Null-count summary table:")
    print(report.to_string())

    flagged = report[report["over_90pct"]]
    print(f"\nColumns above {MISSING_THRESHOLD:.0f}% null: {len(flagged)}")
    if len(flagged):
        print(flagged[["null_pct", "decision"]].to_string())

    out = os.path.join(REPORT_DIR, f"{label.lower()}_missing_report.csv")
    report.to_csv(out, index_label="column")
    print(f"\nSaved: {out}")

    to_drop = report.index[report["decision"] == "drop"].tolist()
    return to_drop

# 4. Numeric distribution review
def numeric_distributions(df, label):
    section(f"{label}: NUMERIC DISTRIBUTIONS")
    fields = [f for f in NUMERIC_FIELDS if f in df.columns]
    missing_fields = set(NUMERIC_FIELDS) - set(fields)
    if missing_fields:
        print(f"Not present in this dataset: {sorted(missing_fields)}")

    rows, outlier_rows = [], []
    for col in fields:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            continue
        q = s.quantile(PERCENTILES)
        rows.append({
            "field": col, "count": len(s), "min": s.min(),
            **{f"p{int(p*100)}": q[p] for p in PERCENTILES},
            "max": s.max(), "mean": s.mean(), "median": s.median(),
        })

        # Finding Outliers
        q1, q3 = q[0.25], q[0.75]
        iqr = q3 - q1
        low, high = q1 - 3 * iqr, q3 + 3 * iqr
        n_low, n_high = (s < low).sum(), (s > high).sum()
        outlier_rows.append({
            "field": col, "lower_fence": low, "upper_fence": high,
            "n_below": n_low, "n_above": n_high,
            "pct_outlier": round((n_low + n_high) / len(s) * 100, 2),
        })

        # Histogram + boxplot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        s.clip(q[0.01], q[0.99]).hist(bins=50, ax=ax1)
        ax1.set_title(f"{col} histogram (clipped to p1–p99)")
        ax1.set_xlabel(col)
        ax2.boxplot(s, vert=False)
        ax2.set_title(f"{col} boxplot (all values)")
        ax2.set_xlabel(col)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG_DIR, f"{label.lower()}_{col}.png"), dpi=100)
        plt.close(fig)

    summary = pd.DataFrame(rows).set_index("field")
    outliers = pd.DataFrame(outlier_rows).set_index("field")

    print("Percentile summary (all reviewed fields):")
    print(summary.round(2).to_string())

    print(f"\nDeliverable summary table – {', '.join(SUMMARY_FIELDS)}:")
    print(summary.loc[[f for f in SUMMARY_FIELDS if f in summary.index],
                      ["min", "p25", "median", "mean", "p75", "p95", "p99", "max"]]
          .round(2).to_string())

    print("\nExtreme outliers (beyond 3×IQR) – flagged for handling in cleaning:")
    print(outliers.round(2).to_string())

    summary.to_csv(os.path.join(REPORT_DIR, f"{label.lower()}_numeric_summary.csv"))
    outliers.to_csv(os.path.join(REPORT_DIR, f"{label.lower()}_outliers.csv"))
    print(f"\nFigures saved to {FIG_DIR}/")

# 5. Suggested intern questions (Sold data)
def eda_questions(sold_raw, sold):
    section("SUGGESTED EDA QUESTIONS (Sold)")

    # Q1 – Residential vs other share
    res_share = (sold_raw["PropertyType"] == "Residential").mean() * 100
    print(f"Q1. Residential share of all sold records: {res_share:.2f}% "
          f"(other types: {100 - res_share:.2f}%)")

    # Q2 – Median and average close price
    cp = pd.to_numeric(sold["ClosePrice"], errors="coerce")
    print(f"\nQ2. Median ClosePrice: ${cp.median():,.0f}   "
          f"Average ClosePrice: ${cp.mean():,.0f}")
    print("    (Mean above median indicates right skew from high-priced sales.)")

    # Q3 – Days on Market distribution
    dom = pd.to_numeric(sold["DaysOnMarket"], errors="coerce").dropna()
    bins = [-float("inf"), -1, 7, 14, 30, 60, 90, 180, 365, float("inf")]
    labels = ["<0 (invalid)", "0–7", "8–14", "15–30", "31–60", "61–90",
              "91–180", "181–365", "365+"]
    dist = pd.cut(dom, bins=bins, labels=labels).value_counts().reindex(labels)
    print(f"\nQ3. Days on Market: median {dom.median():.0f}, mean {dom.mean():.1f}")
    print(pd.DataFrame({"count": dist,
                        "pct": (dist / len(dom) * 100).round(2)}).to_string())

    # Q4 – Sold above / at / below list price
    lp = pd.to_numeric(sold["ListPrice"], errors="coerce")
    valid = (cp > 0) & (lp > 0)
    ratio = cp[valid] / lp[valid]
    print(f"\nQ4. Sale-to-list comparison ({valid.sum():,} rows with both prices > 0):")
    print(f"    Above list: {(ratio > 1).mean() * 100:.2f}%")
    print(f"    At list:    {(ratio == 1).mean() * 100:.2f}%")
    print(f"    Below list: {(ratio < 1).mean() * 100:.2f}%")
    print(f"    Median close-to-list ratio: {ratio.median():.3f}")

    # Q5 – Date consistency
    print("\nQ5. Date consistency checks:")
    dates = {c: pd.to_datetime(sold[c], errors="coerce")
             for c in ["ListingContractDate", "PurchaseContractDate", "CloseDate"]
             if c in sold.columns}
    checks = [
        ("CloseDate before ListingContractDate", "CloseDate", "ListingContractDate"),
        ("PurchaseContractDate before ListingContractDate", "PurchaseContractDate", "ListingContractDate"),
        ("CloseDate before PurchaseContractDate", "CloseDate", "PurchaseContractDate"),
    ]
    for name, later, earlier in checks:
        if later in dates and earlier in dates:
            n = (dates[later] < dates[earlier]).sum()
            print(f"    {name}: {n:,} rows ({n / len(sold) * 100:.2f}%)")
    for c, d in dates.items():
        print(f"    {c} missing or unparseable: {d.isna().sum():,}")

    # Q6 – Counties with highest median close price
    if "CountyOrParish" in sold.columns:
        county = (sold.assign(ClosePrice=cp)
                  .groupby("CountyOrParish")["ClosePrice"]
                  .agg(median="median", sales="count")
                  .query("sales >= 30")              # skip tiny samples
                  .sort_values("median", ascending=False))
        print("\nQ6. Top 10 counties by median ClosePrice (min 30 sales):")
        print(county.head(10).to_string(formatters={"median": "${:,.0f}".format}))
        county.to_csv(os.path.join(REPORT_DIR, "sold_county_medians.csv"))

# Main
def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    section("LOADING RAW MONTHLY FILES")
    sold_raw = load_folder(SOLD_DIR, "CRMLSSold")
    listings_raw = load_folder(LISTED_DIR, "CRMLSListing")

    results = {}
    for label, raw in [("Sold", sold_raw), ("Listings", listings_raw)]:
        describe_structure(raw, label)
        filtered = property_types_and_filter(raw, label)
        to_drop = missing_value_report(filtered, label)
        numeric_distributions(filtered, label)
        results[label] = (filtered, to_drop)

    eda_questions(sold_raw, results["Sold"][0])

    section("SAVING FILTERED DATASETS")
    for label, (df, to_drop) in results.items():
        cleaned = df.drop(columns=to_drop)
        prefix = "CRMLSSold" if label == "Sold" else "CRMLSListing"
        out = os.path.join(OUTPUT_DIR, f"{prefix}_Residential_Validated.csv")
        cleaned.to_csv(out, index=False)
        print(f"{label}: dropped {len(to_drop)} high-missing columns -> "
              f"{cleaned.shape[0]:,} rows × {cleaned.shape[1]} columns")
        print(f"  Saved: {out}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# FINDINGS LOG  (fill in from the printed output after running)
# ---------------------------------------------------------------------------
# Property types found (Sold):     736,481
# Residential share (Sold):        67.12%
# Rows before / after filter:      735,481 / 242,138
# Columns > 90% null / Null-count summary table:
#                              null_count  null_pct    dtype    core_field decision
#FireplacesTotal                   494343    100.00  float64    False      drop
#TaxAnnualAmount                   494343    100.00  float64    False      drop
#AboveGradeFinishedArea            494343    100.00  float64    False      drop
#ElementarySchoolDistrict          494343    100.00  float64    False      drop
#usinessType                      494343    100.00   object    False      drop
#CoveredSpaces                     494343    100.00  float64    False      drop
#MiddleOrJuniorSchoolDistrict      494343    100.00  float64    False      drop
#TaxYear                           494343    100.00  float64    False      drop
#WaterfrontYN                      494030     99.94   object    False      drop
#BelowGradeFinishedArea            491322     99.39  float64    False      drop
#BasementYN                        484643     98.04   object    False      drop
#BuyerAgencyCompensation           481284     97.36  float64    False      drop
#BuyerAgencyCompensationType       481282     97.36   object    False      drop
#BuilderName                       470119     95.10   object    False      drop
#LotSizeDimensions                 470069     95.09   object    False      drop
#BuildingAreaTotal                 459392     92.93  float64    False      drop
#CoBuyerAgentFirstName             448698     90.77   object    False      drop

# ClosePrice    min 0       median 820000.0  mean 1181498.73  max  989500000.0
# LivingArea    min 0       median 1647.0    mean 1901.98     max  17021321.0
# DaysOnMarket  min -288.0  median 19.0      mean 347.72      max  12430.0