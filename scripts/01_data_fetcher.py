import os
import requests
import json
import geopandas as gpd

# Define the output directory relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Overpass API endpoint
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def fetch_osm_power_infrastructure():
    print("Fetching power infrastructure for India from OpenStreetMap...")
    print("Note: This might take a while due to the national scale.")
    
    # Overpass QL Query for India's high voltage transmission network and substations
    overpass_query = """
    [out:json][timeout:900];
    area["name"="India"]->.searchArea;
    (
      way["power"="line"](area.searchArea);
      relation["power"="line"](area.searchArea);
      node["power"="substation"](area.searchArea);
      way["power"="substation"](area.searchArea);
      relation["power"="substation"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """
    
    try:
        response = requests.post(OVERPASS_URL, data={'data': overpass_query}, timeout=950)
        
        if response.status_code == 200:
            output_file = os.path.join(OUTPUT_DIR, "india_power_infrastructure.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f)
            print(f"Successfully downloaded raw OSM power data to {output_file}")
        else:
            print(f"Error fetching power data: HTTP {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def fetch_existing_solar_farms():
    print("Fetching existing solar/wind farms for ML positive labels...")
    
    overpass_query = """
    [out:json][timeout:900];
    area["name"="India"]->.searchArea;
    (
      way["generator:source"="solar"](area.searchArea);
      relation["generator:source"="solar"](area.searchArea);
      node["generator:source"="solar"](area.searchArea);
      
      way["generator:source"="wind"](area.searchArea);
      relation["generator:source"="wind"](area.searchArea);
      node["generator:source"="wind"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """
    
    try:
        response = requests.post(OVERPASS_URL, data={'data': overpass_query}, timeout=950)
        
        if response.status_code == 200:
            output_file = os.path.join(OUTPUT_DIR, "india_existing_renewables.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f)
            print(f"Successfully downloaded raw OSM renewables data to {output_file}")
        else:
            print(f"Error fetching renewables data: HTTP {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    fetch_osm_power_infrastructure()
    fetch_existing_solar_farms()
    print("Data fetching complete.")
