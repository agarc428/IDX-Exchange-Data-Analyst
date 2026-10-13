"""
Ariana Garcia Villabla
IDX

Week 3 Deliverables
------------------------------------
Objective: Fetch the FRED MORTGAGE30US series, resample it from weekly to 
monthly frequency, and merge it onto both combined datasets using a 
year-month key derived from transaction dates.
"""

import pandas as pd

SOLD_DIR = pd.read_csv("Week 2 Deliverables/CRMLSSold_Residential_Validated.csv")
LISTINGS_DIR = pd.read_csv("Week 2 Deliverables/CRMLSListing_Residential_Validated.csv")

url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=['observation_date'])
mortgage.columns = ['date', 'rate_30yr_fixed']

mortgage['year_month'] = mortgage['date'].dt.to_period('M')
mortgage_monthly = (
    mortgage.groupby('year_month')['rate_30yr_fixed']
    .mean()
    .reset_index()
)

SOLD_DIR['year_month'] = pd.to_datetime(SOLD_DIR['CloseDate']).dt.to_period('M')

LISTINGS_DIR['year_month'] = pd.to_datetime(
    LISTINGS_DIR['ListingContractDate']
).dt.to_period('M')

sold_with_rates = SOLD_DIR.merge(mortgage_monthly, on='year_month', how='left')
listings_with_rates = LISTINGS_DIR.merge(mortgage_monthly, on='year_month', how='left')

print(sold_with_rates['rate_30yr_fixed'].isnull().sum())
print(listings_with_rates['rate_30yr_fixed'].isnull().sum())

print(
    sold_with_rates[
        ['CloseDate', 'year_month', 'ClosePrice', 'rate_30yr_fixed']
    ].head()
)

#Saving updated datasets to CSV files as Week 3 Deliverables
sold_with_rates.to_csv("sold_with_rates.csv", index=False)
listings_with_rates.to_csv("listings_with_rates.csv", index=False)