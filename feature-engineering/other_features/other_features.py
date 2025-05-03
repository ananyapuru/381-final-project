import json
import pandas as pd
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# dataset after first round of feature enrichment
housing_df = pd.read_csv("../foursquare/foursquare_enriched_dataset.csv")

# add median household income for USA
# this data is from the 2023 census
def median_income_enrichment_usa(df):
    from census import Census

    # the API key for the USA census
    CENSUS_API_KEY = "c19ab8188ce9ae21aa596415d947236eafa47a6e"
    c = Census(CENSUS_API_KEY)

    # batch all ZCTAs from ACS for merging, median household income
    print("Fetching all ZIP-level income data from ACS (USA Census)...")
    MEDIAN_INCOME = "B19013_001E"
    acs_data = c.acs5.get(
        fields=["NAME", MEDIAN_INCOME],
        geo={"for": "zip code tabulation area:*"},
        year=2023
    )
    median_income_df = pd.DataFrame(acs_data)
    median_income_df.rename(columns={
        "zip code tabulation area": "postcode",
        MEDIAN_INCOME: "median_income_tmp"
    }, inplace=True)

    df.loc[df["country"] == "USA", "postcode"] = df.loc[df["country"] == "USA", "postcode"]
    return df.merge(median_income_df[["postcode", "median_income_tmp"]], on="postcode", how="left")


# add median household income for London
# this data is from 2020, first query postcodes.io for MSOA code (Middle Super Output Area)
# then use MSOA code to extract median household income by postcode
# post-process to dollars
def get_london_msoa(df):
    london_df = df[df["city"] == "London"].copy()
    london_df["postcode"] = london_df["postcode"].astype(str).str.replace(" ", "").str.upper()

    # query api.postcodes.io for MSOA codes for each postcode
    print("Fetching MSOAs for London postcodes...")
    msoa_map = {}
    count = 0
    for pc in london_df["postcode"].unique():
        count += 1
        print(count)
        try:
            res = requests.get(f"https://api.postcodes.io/postcodes/{pc}")
            if res.status_code == 200:
                result = res.json().get("result")
                if result and result.get("msoa"):
                    msoa_map[pc] = result["codes"]["msoa"]
        except Exception as e:
            print(f"Error with postcode {pc}: {e}")
        time.sleep(0.1)

    with open("london_postcode_to_msoa.json", "w") as f:
        json.dump(msoa_map, f)

def median_income_enrichment_london(df, income_by_msoa_file_path):
    # modify column to London postcodes are just one string without spaces
    df.loc[df["city"] == "London", "postcode"] = (
        df.loc[df["city"] == "London", "postcode"]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.upper()
    )

    london_df = df[df["city"] == "London"].copy()
    london_df["postcode"] = london_df["postcode"].astype(str).str.replace(" ", "").str.upper()

    # only call this once! find postcode to MSOA mapping
    # it takes like 20 minutes so don't redo after generating initial JSON file
    # get_london_msoa(df)

    # load in the MSOA map
    with open("london_postcode_to_msoa.json", "r") as f:
        msoa_map = json.load(f)
    london_df["msoa"] = london_df["postcode"].map(msoa_map)

    # create new df with MSOA codes
    print("Fetching all ZIP-level income data from CSV file (London)...")
    income_df = pd.read_csv(income_by_msoa_file_path, delimiter=";")
    income_df.rename(columns={"MSOA code": "msoa"}, inplace=True)

    # merge df with MSOA codes to original df
    enriched_london = london_df.merge(income_df, on="msoa", how="left")
    enriched_london.rename(columns={"Total annual income (£)": "median_income_tmp"}, inplace=True)

    # clean up the median_income_tmp column, convert to dollars
    EXCHANGE_RATE = 1.25
    enriched_london["median_income_tmp"] = (enriched_london["median_income_tmp"].astype(float) * EXCHANGE_RATE * 1000)

    df.loc[df["country"] == "UK", "postcode"] = df.loc[df["country"] == "UK", "postcode"]
    return df.merge(enriched_london[["postcode", "median_income_tmp"]], on="postcode", how="left")


# add median individual income for Australia
# ATO Individuals Table 25
def median_income_enrichment_aus(df):
    print("Fetching all ZIP-level income data from CSV file (Australia)...")
    aus_income_df = pd.read_csv("australia_postcode_values.csv")
    aus_income_df.rename(columns={"Postcode": "postcode", "Median taxable income or loss": "median_income_tmp"}, inplace=True)
    aus_income_df["postcode"] = aus_income_df["postcode"].astype(str)

    df.loc[df["country"] == "Australia", "postcode"] = df.loc[df["country"] == "Australia", "postcode"]
    return df.merge(aus_income_df[["postcode", "median_income_tmp"]], on="postcode", how="left")


# process the postcodes so they are all strings
housing_df["postcode"] = housing_df["postcode"].astype(str)
housing_df.loc[housing_df["country"] == "USA", "postcode"] = housing_df.loc[housing_df["country"] == "USA", "postcode"].astype(str).str[:-2]
housing_df.loc[housing_df["country"] == "Australia", "postcode"] = housing_df.loc[housing_df["country"] == "Australia", "postcode"].astype(str).str[:-2]

# apply enrichment for all three countries
housing_df["median_income"] = None

housing_df = median_income_enrichment_usa(housing_df)
housing_df["median_income"] = housing_df["median_income"].combine_first(housing_df["median_income_tmp"])
housing_df.drop(columns=["median_income_tmp"], inplace=True)

housing_df = median_income_enrichment_london(housing_df, "uk_msoa_median_household_income.csv")
housing_df["median_income"] = housing_df["median_income"].combine_first(housing_df["median_income_tmp"])
housing_df.drop(columns=["median_income_tmp"], inplace=True)

housing_df = median_income_enrichment_aus(housing_df)
housing_df["median_income"] = housing_df["median_income"].combine_first(housing_df["median_income_tmp"])
housing_df.drop(columns=["median_income_tmp"], inplace=True)

# save new file
housing_df.to_csv("final_enriched_dataset.csv", index=False)
