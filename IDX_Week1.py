"""
Ariana Garcia Villabla
IDX

Week 1 Deliverables
------------------------------------
Objective: Load and concatenate all monthly MLS files from
 January 2024 through the most recently completed calendar 
 month into analysis-ready combined datasets.
"""

import glob
import os
import re

import pandas as pd

# Configuration
SOLD_DIR = "C:/Users/Arri7/OneDrive/Desktop/IDX_DA61/csv/CRML_Sold"
LISTED_DIR = "C:/Users/Arri7/OneDrive/Desktop/IDX_DA61/csv/CRML_Listed"
OUTPUT_DIR = "Week 1 Deliverables"              # folder to write the combined CSVs


# Find files in a folder and check for missing months
def find_monthly_files(folder, prefix):
    """
    Return a sorted list of (YYYYMM, path) for files named <prefix>YYYYMM.csv.
    Warns if any month is missing between the first and last file found.
    """
    pattern = re.compile(rf"^{prefix}(\d{{6}})\.csv$")
    files = []
    for path in glob.glob(os.path.join(folder, f"{prefix}*.csv")):
        match = pattern.match(os.path.basename(path))
        if match:
            files.append((match.group(1), path))

    if not files:
        raise FileNotFoundError(f"No {prefix}YYYYMM.csv files found in {folder}")

    files.sort()  

    found = {ym for ym, _ in files}
    y, m = int(files[0][0][:4]), int(files[0][0][4:])
    last = files[-1][0]
    while f"{y}{m:02d}" <= last:
        if f"{y}{m:02d}" not in found:
            print(f"  WARNING: {prefix}{y}{m:02d}.csv is missing from {folder}")
        m += 1
        if m > 12:
            y, m = y + 1, 1

    return files


# Load and concatenate one dataset type (Sold or Listing)
def load_and_concat(folder, prefix):
    """
    Read every monthly file in a folder, print each file's row count,
    and concatenate. Returns (combined_df, row_sum_before, first_ym, last_ym).
    """
    files = find_monthly_files(folder, prefix)
    print(f"  {len(files)} files: {files[0][0]} through {files[-1][0]}")

    frames = []
    total_rows_before = 0
    for ym, path in files:
        df = pd.read_csv(path, low_memory=False)
        df["SourceMonth"] = ym      
        print(f"  {os.path.basename(path)}: {len(df):,} rows")
        total_rows_before += len(df)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    assert len(combined) == total_rows_before, (
        f"{prefix}: row mismatch after concat "
        f"({len(combined):,} vs {total_rows_before:,})"
    )
    return combined, total_rows_before, files[0][0], files[-1][0]


def filter_residential(df, label):
    """Keep only PropertyType == 'Residential' and report row counts."""
    before = len(df)
    filtered = df[df["PropertyType"] == "Residential"].copy()
    after = len(filtered)
    print(f"  {label} before Residential filter: {before:,} rows")
    print(f"  {label} after  Residential filter: {after:,} rows "
          f"({before - after:,} non-Residential rows removed)")
    return filtered


# Main
def main():
    # ----- Sold -----
    print(f"Loading SOLD files from {SOLD_DIR}/ ...")
    sold, sold_rows_before, s_first, s_last = load_and_concat(SOLD_DIR, "CRMLSSold")
    print(f"  Sum of monthly SOLD rows (before concat): {sold_rows_before:,}")
    print(f"  Combined SOLD rows (after concat):        {len(sold):,}\n")

    # ----- Listings -----
    print(f"Loading LISTING files from {LISTED_DIR}/ ...")
    listings, list_rows_before, l_first, l_last = load_and_concat(LISTED_DIR, "CRMLSListing")
    print(f"  Sum of monthly LISTING rows (before concat): {list_rows_before:,}")
    print(f"  Combined LISTING rows (after concat):        {len(listings):,}\n")

    # ----- Residential filter -----
    print("Filtering to PropertyType == 'Residential'...")
    sold_res = filter_residential(sold, "SOLD")
    listings_res = filter_residential(listings, "LISTING")
    print()

    # ----- Save -----
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sold_out = os.path.join(OUTPUT_DIR, f"CRMLSSold_Residential_{s_first}_{s_last}.csv")
    list_out = os.path.join(OUTPUT_DIR, f"CRMLSListing_Residential_{l_first}_{l_last}.csv")
    sold_res.to_csv(sold_out, index=False)
    listings_res.to_csv(list_out, index=False)
    print(f"Saved: {sold_out} ({len(sold_res):,} rows)")
    print(f"Saved: {list_out} ({len(listings_res):,} rows)")


if __name__ == "__main__":
    main()


# ROW COUNT LOG  

# Months covered: 202401 – 202604
#
# SOLD
#   Sum of monthly rows before concatenation:  736,481
#   Rows after concatenation:                  736,481
#   Rows before Residential filter:            736,481
#   Rows after Residential filter:             494,343
#
# LISTINGS
#   Sum of monthly rows before concatenation:  1,021,765
#   Rows after concatenation:                  1,021,765
#   Rows before Residential filter:            1,021,765
#   Rows after Residential filter:             649,615