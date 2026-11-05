"""
Ariana Garcia Villabla
IDX

Week 4/5 Deliverables
------------------------------------

Overview: Weeks 4-5 Data Cleaning and Preparation
Raw MLS data contains formatting inconsistencies, missing values, and fields
 that need transformation before analysis. This phase prepares the dataset 
 for reliable analytics.

Objective: Submit a cleaned, analysis-ready dataset as a CSV, plus a .py 
script documenting every transformation made and why. Include before/after row 
counts, data type confirmations, date consistency flag counts, and a geographic 
data quality summary noting any invalid coordinate records.
"""

"""
Ariana Garcia Villabla
IDX

Weeks 4-5 Deliverables
------------------------------------
Objective: Clean and prepare the MLS Sold dataset for reliable analytics.
"""

import os

import pandas as pd

INPUT_FILE = "sold_with_rates.csv"
OUTPUT_DIR = "Weeks 4-5 Deliverables"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "CRMLSSold_Residential_Cleaned.csv")

DATE_FIELDS = [
    "CloseDate", "PurchaseContractDate",
    "ListingContractDate", "ContractStatusChangeDate",
]

NUMERIC_FIELDS = [
    "ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
    "LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger",
    "DaysOnMarket", "YearBuilt", "Latitude", "Longitude",
]

DROP_COLUMNS = [
    "ListAgentFirstName", "ListAgentLastName", "ListAgentFullName",
    "CoListAgentFirstName", "CoListAgentLastName",
    "BuyerAgentFirstName", "BuyerAgentLastName", "BuyerAgentMlsId",
    "CoListOfficeName",
    "ListingKeyNumeric", "LotSizeArea", "LotSizeSquareFeet",
    "OriginatingSystemName", "OriginatingSystemSubName",
]


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# Task: Convert date fields to datetime format
def convert_dates(sold):
    for col in DATE_FIELDS:
        sold[col] = pd.to_datetime(sold[col])
    return sold


# Task: Remove unnecessary or redundant columns
def remove_columns(sold):
    return sold.drop(columns=[c for c in DROP_COLUMNS if c in sold.columns])


# Task: Ensure numeric fields are properly typed
def convert_numerics(sold):
    for col in NUMERIC_FIELDS:
        sold[col] = pd.to_numeric(sold[col], errors="coerce")
    return sold


# Task: Handle missing values appropriately
def handle_missing(sold):
    return sold.dropna(subset=["ClosePrice", "CloseDate"])


# Task: Remove invalid numeric values
def remove_invalid_numerics(sold):
    invalid = (
        (sold["ClosePrice"] <= 0)
        | (sold["LivingArea"] <= 0)
        | (sold["DaysOnMarket"] < 0)
        | (sold["BedroomsTotal"] < 0)
        | (sold["BathroomsTotalInteger"] < 0)
    )
    return sold[~invalid].copy()


# Date Consistency Checks
def flag_date_consistency(sold):
    sold["listing_after_close_flag"] = sold["ListingContractDate"] > sold["CloseDate"]
    sold["purchase_after_close_flag"] = sold["PurchaseContractDate"] > sold["CloseDate"]
    sold["negative_timeline_flag"] = sold["ListingContractDate"] > sold["PurchaseContractDate"]

    section("DATE CONSISTENCY FLAGS")
    print(sold.filter(like="after_close_flag").join(sold["negative_timeline_flag"])
          .sum().to_string())
    return sold


# Geographic Data Checks
def flag_geography(sold):
    lat, lon = sold["Latitude"], sold["Longitude"]
    sold["missing_coords_flag"] = lat.isna() | lon.isna()
    sold["zero_coords_flag"] = (lat == 0) | (lon == 0)
    sold["positive_longitude_flag"] = lon > 0
    sold["out_of_state_flag"] = (
        ~sold["missing_coords_flag"]
        & ~sold["zero_coords_flag"]
        & ~(lat.between(32.5, 42.0) & lon.between(-124.5, -114.1))
    )

    geo_flags = ["missing_coords_flag", "zero_coords_flag",
                 "positive_longitude_flag", "out_of_state_flag"]
    section("GEOGRAPHIC DATA QUALITY")
    print(sold[geo_flags].sum().to_string())
    print(f"Records with any invalid coordinate: {sold[geo_flags].any(axis=1).sum():,}")
    return sold


def confirm_dtypes(sold):
    section("DATA TYPES")
    print(sold[DATE_FIELDS + NUMERIC_FIELDS].dtypes.to_string())


def main():
    section("LOADING")
    sold = pd.read_csv(INPUT_FILE, low_memory=False)
    rows_before = len(sold)
    print(f"  {INPUT_FILE}: {rows_before:,} rows x {sold.shape[1]} columns")

    sold = convert_dates(sold)
    sold = remove_columns(sold)
    sold = convert_numerics(sold)
    sold = handle_missing(sold)
    sold = remove_invalid_numerics(sold)
    sold = flag_date_consistency(sold)
    sold = flag_geography(sold)
    confirm_dtypes(sold)

    section("SUMMARY")
    print(f"  Rows before cleaning: {rows_before:,}")
    print(f"  Rows after cleaning:  {len(sold):,}")
    print(f"  Rows removed:         {rows_before - len(sold):,}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sold.to_csv(OUTPUT_FILE, index=False)
    print(f"  Saved: {OUTPUT_FILE} ({len(sold):,} rows x {sold.shape[1]} columns)")


if __name__ == "__main__":
    main()