# geocoder.py
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd

"""
Takes in Original Dataset and Adds Latitute and Longitude information (Geolocation Data)
Creates a new CSV file and outputs the modified dataset in geocoded_dataset.csv
"""

OUTPUT_FILENAME = 'geocoded_dataset.csv'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("geocoding.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class RobustPostcodeGeocoder:
    def __init__(self, max_retries=3):
        self.geolocator = Nominatim(user_agent="cpsc381-final-project")
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1/20)
        self.cache = {}
        self.max_retries = max_retries

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _geocode_single(self, postcode, country):
        """Geocode with retries and exponential backoff."""
        cache_key = f"{postcode},{country}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            location = self.geocode(f"{postcode}, {country}", timeout=10)
            if location:
                coords = (location.latitude, location.longitude)
                self.cache[cache_key] = coords
                logger.info(f"Geocoded: {postcode}, {country} → {coords}")
                return coords
            logger.warning(f"No results for: {postcode}, {country}")
            return (None, None)
        except Exception as e:
            logger.error(f"Geocoding attempt failed for {postcode}, {country}: {str(e)}")
            raise

    def _find_nearby_postcodes(self, postcode, country):
        """Fallback postcode generator with country-specific logic."""
        try:
            if country == "UK":
                # Example: SW1A 1AA → SW1A 1AB, SW1A 1AC, etc.
                outward, inward = postcode[:-3].strip(), postcode[-3:]
                return [f"{outward} {chr(ord(inward[0]) + i)}{inward[1:]}" for i in range(1, 4)]
            else: # for australia and the US
                # Example: 90210 → 90211, 90212
                return [str(int(postcode) + i) for i in range(1, 6)]
        except Exception as e:
            logger.error(f"Fallback postcode generation failed: {str(e)}")
            return []

    def geocode_with_fallback(self, postcode, country):
        if country != 'UK':
            postcode = int(float(postcode))
        """Robust geocoding with cascading fallbacks."""
        # first try exact geocode
        try:
            exact_coords = self._geocode_single(postcode, country)
            if exact_coords != (None, None):
                return exact_coords
        except Exception as e:
            logger.warning(f"Primary geocoding failed for {postcode}, {country}. Attempting fallbacks...")

        # then try nearby postcodes
        for fallback_postcode in self._find_nearby_postcodes(postcode, country):
            try:
                fallback_coords = self._geocode_single(fallback_postcode, country)
                if fallback_coords != (None, None):
                    logger.info(f"Used fallback: {postcode} → {fallback_postcode}")
                    return fallback_coords
            except Exception as e:
                logger.error(f"Fallback failed for {fallback_postcode}: {str(e)}")
                continue

        # Lastly Approximate centroid
        try:
            country_coords = {
                "UK": (54.0, -2.5),
                "US": (37.6, -95.7),
                "Australia": (-25.3, 133.8)
            }.get(country, (None, None))

            if country_coords != (None, None):
                logger.warning(f"Using country centroid for {postcode}, {country}")
                return country_coords
        except Exception as e:
            logger.critical(f"All fallbacks exhausted for {postcode}, {country}")
        return (None, None)

    def batch_geocode(self, df, postcode_col="postcode", country_col="country"):
        """Process DataFrame with atomic error handling."""
        results = []
        failed_indices = []

        for idx, row in df.iterrows():
            try:
                coords = self.geocode_with_fallback(row[postcode_col], row[country_col])
                results.append({**row.to_dict(), "latitude": coords[0], "longitude": coords[1]})
            except Exception as e:
                logger.error(f"Row {idx} failed: {str(e)}")
                failed_indices.append(idx)
                results.append({**row.to_dict(), "latitude": None, "longitude": None})

        logger.info(f"Completed. Failed rows: {len(failed_indices)}/{len(df)}")
        return pd.DataFrame(results), failed_indices

if __name__ == "__main__":
    geocoder = RobustPostcodeGeocoder(max_retries=3)
    df = pd.read_csv('original_dataset.csv', dtype=str)
    result_df, failed = geocoder.batch_geocode(df)
    result_df.to_csv(OUTPUT_FILENAME)
    if failed:
        print(f"\nFailed rows: {failed}")
