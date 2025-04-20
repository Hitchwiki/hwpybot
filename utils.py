from geopy.geocoders import Nominatim
import requests


geolocator = Nominatim(user_agent="country_locator")

# Function to get coordinates
def get_country_coordinates(country_name):
    try:
        location = geolocator.geocode(country_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except Exception as e:
        print(f"Error retrieving coordinates for {country_name}: {e}")
        return None


def get_english_city_name(german_name):
    try:
        query = f"""
        SELECT ?cityLabel WHERE {{
        ?city rdfs:label "{german_name}"@de.
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        url = "https://query.wikidata.org/sparql"
        headers = {"Accept": "application/json"}
        response = requests.get(url, params={'query': query}, headers=headers)
        
        data = response.json()
        results = data.get('results', {}).get('bindings', [])
        if results:
            return results[0]['cityLabel']['value']
        else:
            return german_name  # fallback if not found
    except Exception as e:
        print(f"Error retrieving English city name for {german_name}: {e}")
        return german_name