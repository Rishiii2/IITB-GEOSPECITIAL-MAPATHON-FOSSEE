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
    """Extract power lines, substations, and solar/wind farms from PBF using pyogrio (streaming)"""
    print("Parsing OSM PBF data using pyogrio and GDAL (Memory Efficient)...")
    try:
        import pyogrio
    except ImportError:
        print("Error: 'pyogrio' is not installed. Please run 'pip install pyogrio'")
        return

    # In GDAL's OSM driver, tags not defined in osmconf.ini go into the 'other_tags' column.
    # We use a SQL-like WHERE clause to filter them out during the C++ read phase, bypassing python memory limits!
    
    out_power = os.path.join(RAW_DIR, "india_power_infrastructure.gpkg")
    out_renewables = os.path.join(RAW_DIR, "india_existing_renewables.gpkg")

    # 1. Extract Power Lines (usually represented as LineStrings)
    print("Extracting high voltage power lines...")
    try:
        power_lines = pyogrio.read_dataframe(
            PBF_PATH, 
            layer="lines",
            where="other_tags LIKE '%\"power\"=>\"line\"%' OR power='line'"
        )
        if not power_lines.empty:
            power_lines.to_file(out_power, driver="GPKG", layer="power_lines")
            print(f"  -> Saved {len(power_lines)} power lines.")
    except Exception as e:
        print(f"Error reading power lines: {e}")

    # 2. Extract Substations (can be points or polygons)
    print("Extracting substations (points)...")
    try:
        substations_pt = pyogrio.read_dataframe(
            PBF_PATH, 
            layer="points",
            where="other_tags LIKE '%\"power\"=>\"substation\"%' OR power='substation'"
        )
        if not substations_pt.empty:
            substations_pt.to_file(out_power, driver="GPKG", layer="substations_points")
            print(f"  -> Saved {len(substations_pt)} substations (points).")
    except Exception as e:
        pass

    # 3. Extract existing renewables (Solar/Wind Farms - usually polygons)
    print("Extracting existing solar and wind farms (polygons)...")
    try:
        solar_wind = pyogrio.read_dataframe(
            PBF_PATH, 
            layer="multipolygons",
            where="other_tags LIKE '%\"generator:source\"=>\"solar\"%' OR other_tags LIKE '%\"generator:source\"=>\"wind\"%'"
        )
        if not solar_wind.empty:
            solar_wind.to_file(out_renewables, driver="GPKG", layer="solar_wind_farms")
            print(f"  -> Saved {len(solar_wind)} renewable farms.")
    except Exception as e:
        print(f"Error reading solar/wind farms: {e}")

if __name__ == "__main__":
    download_geofabrik_data()
    parse_osm_data()
    print("Geofabrik Data Pipeline complete.")
