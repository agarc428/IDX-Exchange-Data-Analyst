"""
Ariana Garcia Villabla
IDX

Week 6 Deliverables
------------------------------------
Overview: With clean data in hand, you will engineer the key market indicators that 
power the Tableau dashboards.

Objective: Engineer the key market metrics that power the Tableau
dashboards, add school districts from property coordinates, and
summarize the metrics by market segment.
"""

import os

import geopandas as gpd
import pandas as pd

pd.set_option("display.width", 160)

INPUT_FILE = "Weeks 4-5 Deliverables/CRMLSSold_Residential_Cleaned.csv"
OUTPUT_DIR = "Week 6 Deliverables"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "CRMLSSold_Residential_Features.csv")

# California School District Areas
SCHOOL_DISTRICTS_URL = (
    "C:/Users/Arri7/Downloads/DistrictAreas2425/DistrictAreas2425.shp"
)
DISTRICT_NAME_FIELD = "DistrictNa"

DATE_FIELDS = ["CloseDate", "PurchaseContractDate", "ListingContractDate"]

METRIC_COLUMNS = [
    "price_ratio", "close_to_original_list_ratio", "price_per_sqft",
    "DaysOnMarket", "Year", "Month", "YrMo",
    "listing_to_contract_days", "contract_to_close_days",
]

SEGMENTS = {
    "property_type": ["PropertyType", "PropertySubType"],
    "county_area": ["CountyOrParish", "MLSAreaMajor"],
    "offices": ["ListOfficeName", "BuyerOfficeName"],
}


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# Key Metrics to Create
def add_metrics(sold):
    sold["price_ratio"] = sold["ClosePrice"] / sold["OriginalListPrice"]
    sold["close_to_original_list_ratio"] = sold["ClosePrice"] / sold["OriginalListPrice"]
    sold["price_per_sqft"] = sold["ClosePrice"] / sold["LivingArea"]

    sold["Year"] = sold["CloseDate"].dt.year
    sold["Month"] = sold["CloseDate"].dt.month
    sold["YrMo"] = sold["CloseDate"].dt.strftime("%Y-%m")

    sold["listing_to_contract_days"] = (
        sold["PurchaseContractDate"] - sold["ListingContractDate"]
    ).dt.days
    sold["contract_to_close_days"] = (
        sold["CloseDate"] - sold["PurchaseContractDate"]
    ).dt.days
    return sold


# Add school districts using latitude and longitude
def add_school_districts(sold):
    districts = gpd.read_file(SCHOOL_DISTRICTS_URL)
    print(f"School district fields: {list(districts.columns)}")

    points = gpd.GeoDataFrame(
        sold[["Latitude", "Longitude"]],
        geometry=gpd.points_from_xy(sold["Longitude"], sold["Latitude"]),
        crs="EPSG:4326",
    ).to_crs(districts.crs)

    matches = gpd.sjoin(
        points, districts[[DISTRICT_NAME_FIELD, "geometry"]],
        how="left", predicate="within",
    )

    # A property can sit in both an elementary and a high school district,
    # so matches are combined into one value per property.
    sold["SchoolDistrict"] = (
        matches.groupby(level=0)[DISTRICT_NAME_FIELD]
        .agg(lambda names: "; ".join(names.dropna()) or None)
    )
    return sold


# Segment Analysis
def segment_summary(sold, group_cols):
    return (
        sold.groupby(group_cols)
        .agg(
            sales=("ClosePrice", "size"),
            median_close_price=("ClosePrice", "median"),
            median_price_ratio=("price_ratio", "median"),
            median_close_to_original_list_ratio=("close_to_original_list_ratio", "median"),
            median_price_per_sqft=("price_per_sqft", "median"),
            median_days_on_market=("DaysOnMarket", "median"),
            median_listing_to_contract_days=("listing_to_contract_days", "median"),
            median_contract_to_close_days=("contract_to_close_days", "median"),
        )
        .sort_values("sales", ascending=False)
        .round(2)
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    section("LOADING")
    sold = pd.read_csv(INPUT_FILE, low_memory=False, parse_dates=DATE_FIELDS)
    rows_before = len(sold)
    print(f"  {INPUT_FILE}: {rows_before:,} rows x {sold.shape[1]} columns")

    sold = add_metrics(sold)

    section("SCHOOL DISTRICTS")
    sold = add_school_districts(sold)
    assert len(sold) == rows_before, "Row count changed during district join"
    matched = sold["SchoolDistrict"].notna().sum()
    print(f"  Properties matched to a school district: {matched:,} "
          f"({matched / len(sold) * 100:.2f}%)")

    section("SAMPLE OUTPUT – ENGINEERED METRICS")
    sample_cols = (["ClosePrice", "OriginalListPrice", "LivingArea", "CloseDate"]
                   + METRIC_COLUMNS + ["SchoolDistrict"])
    print(sold[sample_cols].dropna(subset=METRIC_COLUMNS).head(10).to_string())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name, group_cols in SEGMENTS.items():
        summary = segment_summary(sold, group_cols)
        section(f"SEGMENT SUMMARY – {' / '.join(group_cols)} (top 10 by sales)")
        print(summary.head(10).to_string())
        summary.to_csv(os.path.join(OUTPUT_DIR, f"segment_{name}.csv"))

    sold.to_csv(OUTPUT_FILE, index=False)
    section("SAVED")
    print(f"  {OUTPUT_FILE} ({len(sold):,} rows x {sold.shape[1]} columns)")
    print(f"  Segment summaries: {OUTPUT_DIR}/segment_*.csv")


if __name__ == "__main__":
    main()