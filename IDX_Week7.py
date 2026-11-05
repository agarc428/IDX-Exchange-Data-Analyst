"""
Ariana Garcia Villabla
IDX

Week 7 Deliverables
------------------------------------
Objective: Identify extreme values in ClosePrice, LivingArea, and
DaysOnMarket using the IQR method, flag them rather than deleting them,
and save both a full flagged dataset and a clean filtered dataset.
"""

import os

import pandas as pd

INPUT_FILE = "Week 6 Deliverables/CRMLSSold_Residential_Features.csv"
OUTPUT_DIR = "Week 7 Deliverables"
FLAGGED_FILE = os.path.join(OUTPUT_DIR, "CRMLSSold_Residential_Flagged.csv")
FILTERED_FILE = os.path.join(OUTPUT_DIR, "CRMLSSold_Residential_Filtered.csv")

IQR_FIELDS = ["ClosePrice", "LivingArea", "DaysOnMarket"]
PERCENTILES = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# Use percentiles alongside IQR to guide decisions
def percentile_review(sold):
    section("PERCENTILES (before filtering)")
    print(sold[IQR_FIELDS].quantile(PERCENTILES).round(2).to_string())


# IQR method: add outlier flag columns rather than deleting records
def flag_iqr_outliers(sold):
    section("IQR FENCES AND OUTLIER FLAGS")
    for col in IQR_FIELDS:
        q1 = sold[col].quantile(0.25)
        q3 = sold[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        flag = f"{col}_outlier_flag"
        sold[flag] = (sold[col] < lower) | (sold[col] > upper)

        n = sold[flag].sum()
        print(f"  {col}: lower {lower:,.2f}  upper {upper:,.2f}  "
              f"flagged {n:,} ({n / len(sold) * 100:.2f}%)")

    sold["any_outlier_flag"] = sold[[f"{c}_outlier_flag" for c in IQR_FIELDS]].any(axis=1)
    print(f"  Records with any outlier flag: {sold['any_outlier_flag'].sum():,}")
    return sold


# Comparison of dataset size and median values before and after filtering
def compare(full, filtered):
    section("BEFORE / AFTER COMPARISON")
    comparison = pd.DataFrame({
        "before": [len(full)] + [full[c].median() for c in IQR_FIELDS],
        "after": [len(filtered)] + [filtered[c].median() for c in IQR_FIELDS],
    }, index=["row_count"] + [f"median_{c}" for c in IQR_FIELDS])
    print(comparison.round(2).to_string())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    section("LOADING")
    sold = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"  {INPUT_FILE}: {len(sold):,} rows x {sold.shape[1]} columns")

    percentile_review(sold)
    sold = flag_iqr_outliers(sold)

    # Separate filtered analysis dataset; the flagged dataset keeps every record
    filtered = sold[~sold["any_outlier_flag"]].copy()

    compare(sold, filtered)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sold.to_csv(FLAGGED_FILE, index=False)
    filtered.to_csv(FILTERED_FILE, index=False)

    section("SAVED")
    print(f"  Full flagged dataset: {FLAGGED_FILE} ({len(sold):,} rows)")
    print(f"  Filtered dataset:     {FILTERED_FILE} ({len(filtered):,} rows)")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# WRITTEN COMPARISON
# ---------------------------------------------------------------------------
# Dataset size: filtering removed 76,291 records (15.44%), from 494,111 to 417,820.
#
# Median ClosePrice moved from $820,000 to $785,000 (-4.27%).
# Median LivingArea moved from 1,647 to 1,574 sq ft (-4.43%).
# Median DaysOnMarket moved from 19 to 16 days (-15.79%).
#
# Interpretation: All three lower IQR fences are negative, so the method
# flagged only the high end: luxury sales above $2.39M, homes over
# 3,690 sq ft, and listings on the market more than 110 days. Removing that
# upper tail lowered every median, with Days on Market shifting most
# (-15.79%) because its distribution is the most right-skewed. The
# percentiles show the low end is plausible (1st percentile: $200,000,
# 610 sq ft), so no low-value records were removed. The filtered dataset
# better represents the typical market, while the flagged dataset keeps
# all 494,111 records for luxury or long-market analysis.