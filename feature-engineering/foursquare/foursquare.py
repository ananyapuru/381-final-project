# foursquare_client.py
import logging
import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("foursquare.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


class FoursquareClient:
    def __init__(self):
        self.access_token = os.getenv("FOURSQUARE_ACCESS_TOKEN")
        self.base_url = "https://api.foursquare.com/v3/places/search"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def get_venues(self, latitude, longitude, radius=1000, limit=50):
        """Query Foursquare API for venues near coordinates."""
        params = {
            "ll": f"{latitude},{longitude}",
            "radius": radius,
            "limit": limit,
            "fields": "name,categories,distance,rating,popularity"
        }

        try:
            logger.info(f"Querying venues near ({latitude:.4f}, {longitude:.4f})")
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            venues = response.json().get('results', [])
            logger.info(f"Found {len(venues)} venues")
            return venues

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return []

    def venues_to_dataframe(self, venues):
        """Convert Foursquare API response to structured DataFrame."""
        records = []
        for venue in venues:
            records.append({
                "venue_name": venue.get('name'),
                "categories": ", ".join([c['name'] for c in venue.get('categories', [])]),
                "distance": venue.get('distance'),  # meters
                "rating": venue.get('rating'),
                "popularity": venue.get('popularity')
            })
        return pd.DataFrame(records)

    def enrich_properties(self, df, radius=1000):
        """Add venue stats to each property."""
        logger.info(f"Enriching {len(df)} properties with Foursquare data")
        results = []

        for idx, row in df.iterrows():
            venues = self.get_venues(row['latitude'], row['longitude'], radius)
            if venues:
                df_venues = self.venues_to_dataframe(venues)
                stats = {
                    "num_venues": len(df_venues),
                    "num_restaurants": len(df_venues[df_venues['categories'].str.contains('restaurant', case=False)]),
                    "avg_rating": df_venues['rating'].mean()
                }
                results.append({**row.to_dict(), **stats})
            time.sleep(1)  # Rate limiting

        return pd.DataFrame(results)


if __name__ == "__main__":
    # Example usage
    client = FoursquareClient()
    test_venues = client.get_venues(51.5014, -0.1419)  # London coordinates
    print(client.venues_to_dataframe(test_venues).head())