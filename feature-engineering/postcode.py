import pandas as pd
import pgeocode
import requests
import censusdata
import datetime
from urllib.parse import quote


def get_crime_rate(postcode, radius_m=1000, year=None, month=None):
    """
    Returns the crime rate (crimes per 1,000 residents per month)
    around a given UK postcode.

    Args:
      postcode (str): e.g. "SW1A 1AA"
      radius_m (int): search radius in metres (default 1000m)
      year (int): e.g. 2025; defaults to current year
      month (int): 1-12; defaults to current month

    Returns:
      dict: {
        'crime_count': int,
        'population': int,
        'crime_rate_per_1000': float
      }
    """
    # 1) Geocode to get lat/lon and LSOA code
    nomi = pgeocode.Nominatim('gb')
    info = nomi.query_postal_code(postcode)

    if pd.isna(info.latitude) or pd.isna(info.longitude):
        raise ValueError(f"Could not geocode postcode: {postcode}")

    lat, lon = info.latitude, info.longitude

    # Get LSOA using postcodes.io API
    lsoa_response = requests.get(f"https://api.postcodes.io/postcodes/{quote(postcode)}")
    if lsoa_response.status_code != 200:
        raise ValueError(f"Could not find LSOA for postcode: {postcode}")

    lsoa = lsoa_response.json()['result']['codes']['lsoa']

    # 2) Fetch all crimes in that radius for the given month
    now = datetime.date.today()
    year = year or now.year
    month = month or now.month
    date_str = f"{year:04d}-{month:02d}"

    crim_url = (
        "https://data.police.uk/api/crimes-street/all-crime"
        f"?lat={lat}&lng={lon}&date={date_str}&radius={radius_m}"
    )

    try:
        crimes = requests.get(crim_url).json()
        crime_count = len(crimes)
    except Exception as e:
        raise ValueError(f"Failed to fetch crime data: {str(e)}")

    # 3) Lookup population of that LSOA from 2021 census
    try:
        pop_df = censusdata.download(
            'Census2021',
            censusdata.censusgeo([('LSOA', lsoa)]),
            ['KS102EW']
        )
        population = int(pop_df['KS102EW'].iloc[0])
    except Exception as e:
        raise ValueError(f"Failed to fetch population data: {str(e)}")

    # 4) Compute rate per 1,000 residents
    rate_per_1000 = crime_count / (population / 1000)

    return {
        'crime_count': crime_count,
        'population': population,
        'crime_rate_per_1000': rate_per_1000
    }

if __name__ == "__main__":
    try:
        stats = get_crime_rate("SW1A 1AA", radius_m=800)
        print(f"{stats['crime_count']} crimes → "
              f"{stats['crime_rate_per_1000']:.2f} per 1,000 residents")
    except Exception as e:
        print(f"Error: {str(e)}")