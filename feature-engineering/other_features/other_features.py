import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# dataset after first round of feature enrichment
housing_df = pd.read_csv("./foursquare/foursquare_enriched_dataset.csv")

# add median household income for USA
def median_income_enrichment_usa(df):
    from census import Census
    from us import states

    # get API for census
    CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
    c = Census(CENSUS_API_KEY)

    # get median household income by ZIP (ZCTA), only get valid ones
    zips = df[df["region"].isin(["NYC", "King County"])]["postal_code"].unique()
    zips = [z[:5] for z in zips if z.isdigit()]

    results = c.acs5.zipcode(("NAME", "B19013_001E"), zips, year=2021)
    income_df = pd.DataFrame(results)
    income_df.rename(columns={"zip code tabulation area": "postal_code",
                              "B19013_001E": "median_income"}, inplace=True)

    return df.merge(income_df[["postcode", "median_income"]], on="postcode", how="left")

def median_income_enrichment_london(df):
    # download manually from London Datastore
    income_df = pd.read_csv("london_income_by_postcode.csv") 
    return df.merge(income_df[["postcode", "median_income"]].rename(columns={"postcode": "postal_code"}), on="postal_code", how="left")

def median_income_enrichment_aus(df):
    # download from ABS
    aus_income_df = pd.read_csv("abs_income_by_postcode.csv")
    return df.merge(aus_income_df[["postcode", "median_income"]].rename(columns={"postcode": "postal_code"}), on="postal_code", how="left")

# apply enrichment for all three countries
housing_df = median_income_enrichment_usa(housing_df)
housing_df = median_income_enrichment_london(housing_df)
housing_df = median_income_enrichment_aus(housing_df)

# save new file
housing_df.to_csv("final_enriched_dataset.csv", index=False)
