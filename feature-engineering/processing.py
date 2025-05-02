import overpass
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import numpy as np

# NOTE: In order to run the following code, proj library/executable is required
# You can install it with brew install proj on Mac

def get_overpass_features(lat, lon, radius=1000):
    """
    Fetch geographic features from OpenStreetMap using Overpass API.
    Returns a dictionary of counts within the specified radius (meters).
    """
    api = overpass.API(timeout=600)

    # Define circular search area
    overpass_query = f"""
    [out:json];
    (
      node(around:{radius},{lat},{lon})["amenity"];
      way(around:{radius},{lat},{lon})["amenity"];
      relation(around:{radius},{lat},{lon})["amenity"];
    );
    out count;
    """

    try:
        result = api.get(overpass_query, verbosity='geom')
        return process_osm_data(result, radius)
    except Exception as e:
        print(f"Overpass query failed: {e}")
        return create_empty_features()


def process_osm_data(osm_json, radius):
    """Convert OSM JSON to feature counts"""
    amenities = {
        'school': 0, 'restaurant': 0, 'pub': 0,
        'bus_stop': 0, 'park': 0, 'supermarket': 0
    }

    for element in osm_json['elements']:
        amenity_type = element.get('tags', {}).get('amenity')
        if amenity_type in amenities:
            amenities[amenity_type] += 1

    # Calculate density features
    area_sqkm = (np.pi * (radius ** 2)) / 1e6
    amenities.update({
        'amenity_density': sum(amenities.values()) / area_sqkm,
        'pub_density': amenities['pub'] / area_sqkm
    })

    return amenities


def create_empty_features():
    """Return empty feature dict when API fails"""
    return {
        'school': np.nan, 'restaurant': np.nan, 'pub': np.nan,
        'bus_stop': np.nan, 'park': np.nan, 'supermarket': np.nan,
        'amenity_density': np.nan, 'pub_density': np.nan
    }


# Enhanced crime function with Overpass integration
def get_enriched_crime_data(postcode, radius=1000):
    """Combine crime data with geographic features"""
    # Get base crime data (from previous implementation)
    crime_data = get_crime_rate(postcode, radius_m=radius)

    # Get geographic coordinates
    nomi = pgeocode.Nominatim('gb')
    geo = nomi.query_postal_code(postcode)

    # Fetch Overpass features
    osm_features = get_overpass_features(geo.latitude, geo.longitude, radius)

    # Combine all features
    return {**crime_data, **osm_features, **{
        'latitude': geo.latitude,
        'longitude': geo.longitude,
        'search_radius_m': radius
    }}


# Example usage
if __name__ == "__main__":
    features = get_enriched_crime_data("SW1A 1AA", 1000)
    print(pd.DataFrame([features]))