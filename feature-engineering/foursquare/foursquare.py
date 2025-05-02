import logging
import requests
import pandas as pd
import time
import os
import json
from pathlib import Path
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
    def __init__(self, cache_file="foursquare_cache.json"):
        self.access_token = os.getenv("FOURSQUARE_API_KEY")
        self.base_url = "https://api.foursquare.com/v3/places/search"
        self.headers = {
            "Authorization": f"{self.access_token}",
            "Accept": "application/json"
        }

        # Broad category groups based on Foursquare ID ranges
        self.category_groups = {
            'dining_drinking': (13000, 13999),  # All food and drink venues
            'retail_shopping': (17000, 17999),  # All retail and shopping
            'education': (12009, 12063),  # Schools, libraries, etc.
            'recreation': (18000, 18999),  # Parks, sports, outdoors
            'entertainment': (10000, 10999),  # Arts, entertainment
            'transportation': (19000, 19999),  # Transit, parking
            'healthcare': (15000, 15999),  # Hospitals, clinics
            'professional': (11000, 11200)  # Offices, banks, etc.
        }

        # Initialize cache
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        """Load cache from file if it exists."""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception:
            return {}
        return {}

    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception:
            pass

    def _get_cache_key(self, latitude, longitude, radius, limit):
        """Generate a consistent cache key."""
        # Approx 11.1 m error (which is fine)
        lat_key = round(float(latitude), 4)
        lng_key = round(float(longitude), 4)
        return f"{lat_key}_{lng_key}_{radius}_{limit}"

    def _is_in_category_range(self, category_id, range_tuple):
        """Check if a category ID falls within a specified range."""
        try:
            category_num = int(category_id)
            return range_tuple[0] <= category_num <= range_tuple[1]
        except (ValueError, TypeError):
            return False

    def get_venues(self, latitude, longitude, radius=1000, limit=50):
        """Query Foursquare API for venues near coordinates."""
        cache_key = self._get_cache_key(latitude, longitude, radius, limit)

        if cache_key in self.cache:
            logger.info(f"Venues found in cache for ({latitude:.4f}, {longitude:.4f})")
            return self.cache[cache_key]

        params = {
            "ll": f"{latitude},{longitude}",
            "radius": radius,
            "limit": limit,
            "fields": "name,categories,distance,rating,popularity,stats,price"
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

            self.cache[cache_key] = venues
            self._save_cache()
            time.sleep(0.5)  # Rate limiting

            return venues

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return []

    def venues_to_dataframe(self, venues):
        """Convert API response to DataFrame with category info."""
        records = []
        for venue in venues:
            categories = venue.get('categories', [])
            primary_category = categories[0] if categories else {}

            records.append({
                "venue_name": venue.get('name'),
                "category_id": primary_category.get('id'),
                "category_name": primary_category.get('name'),
                "distance": venue.get('distance'),
                "rating": venue.get('rating'),
                "popularity": venue.get('popularity'),
                "stats": venue.get('stats', {})
            })
        return pd.DataFrame(records)

    def count_venue_types(self, df_venues):
        """Count venues by broad category groups."""
        stats = {
            "total_venues": len(df_venues),
            "avg_venue_rating": None,
            "avg_venue_popularity": None
        }

        # Calculate overall averages
        if not df_venues['rating'].isna().all():
            stats["avg_venue_rating"] = df_venues['rating'].mean(skipna=True)

        if not df_venues['popularity'].isna().all():
            stats["avg_venue_popularity"] = df_venues['popularity'].mean(skipna=True)

        # Count venues in each broad category group
        for group_name, id_range in self.category_groups.items():
            # Create mask for venues in this category range
            in_category = df_venues['category_id'].apply(
                lambda x: self._is_in_category_range(x, id_range)
            )

            count = in_category.sum()
            stats[f"num_{group_name}"] = count

        # Additional useful metrics
        high_rating_mask = df_venues['rating'].notna() & (df_venues['rating'] >= 8.0)
        stats["num_high_rating_venues"] = high_rating_mask.sum()

        return stats

    def process_csv(self, input_file, output_file, radius=1000, batch_size=None):
        """Process property CSV and enrich with venue data."""
        logger.info(f"Loading input file: {input_file}")
        df = pd.read_csv(input_file)

        if batch_size:
            df = df.head(batch_size)

        results = []

        for idx, row in df.iterrows():
            try:
                venues = self.get_venues(row['latitude'], row['longitude'], radius)
                df_venues = self.venues_to_dataframe(venues)
                venue_stats = self.count_venue_types(df_venues)
                results.append({**row.to_dict(), **venue_stats})

            except Exception as e:
                logger.error(f"Error processing property {idx}: {str(e)}")
                continue

        pd.DataFrame(results).to_csv(output_file, index=False)
        logger.info(f"Saved results to {output_file}")


if __name__ == "__main__":
    client = FoursquareClient()
    input_csv = "geocoded_dataset.csv"
    output_csv = "foursquare_enriched_dataset.csv"
    client.process_csv(input_csv, output_csv, batch_size=None)