import os
import requests
import geopandas as gpd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

GEOFABRIK_URL = "https://download.geofabrik.de/asia/india-latest.osm.pbf"
PBF_PATH = os.path.join(RAW_DIR, "india-latest.osm.pbf")

def download_geofabrik_data():
    """Download the India PBF file from Geofabrik (~1.3 GB)"""
    if os.path.exists(PBF_PATH):
        print(f"File {PBF_PATH} already exists. Skipping download.")
        return
        
    print(f"Downloading India OSM data from Geofabrik (this is >1GB and will take time)...")
    with requests.get(GEOFABRIK_URL, stream=True) as r:
        r.raise_for_status()
        with open(PBF_PATH, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print("Download complete!")

def parse_osm_data():
    """Extract power lines, substations, and solar/wind farms from PBF"""
    print("Parsing OSM PBF data using pyrosm...")
    try:
        from pyrosm import OSM
    except ImportError:
        print("Error: 'pyrosm' is not installed. Please run 'pip install pyrosm'")
        return

    osm = OSM(PBF_PATH)
    
    # 1. Extract power infrastructure (Custom filter)
    print("Extracting high voltage power lines and substations...")
    power_filter = {"power": ["line", "substation"]}
    power_infrastructure = osm.get_data_by_custom_criteria(custom_filter=power_filter, keep_nodes=True, keep_ways=True, keep_relations=True)
    
    if power_infrastructure is not None and not power_infrastructure.empty:
        out_power = os.path.join(RAW_DIR, "india_power_infrastructure.gpkg")
        power_infrastructure.to_file(out_power, driver="GPKG")
        print(f"Saved power infrastructure to {out_power}")
    else:
        print("No power infrastructure found.")

    # 2. Extract existing renewables (Solar/Wind)
    print("Extracting existing solar and wind farms...")
    renewable_filter = {"generator:source": ["solar", "wind"]}
    renewables = osm.get_data_by_custom_criteria(custom_filter=renewable_filter, keep_nodes=True, keep_ways=True, keep_relations=True)
    
    if renewables is not None and not renewables.empty:
        out_renewables = os.path.join(RAW_DIR, "india_existing_renewables.gpkg")
        renewables.to_file(out_renewables, driver="GPKG")
        print(f"Saved renewables to {out_renewables}")
    else:
        print("No renewable farms found.")

if __name__ == "__main__":
    download_geofabrik_data()
    parse_osm_data()
    print("Geofabrik Data Pipeline complete.")
