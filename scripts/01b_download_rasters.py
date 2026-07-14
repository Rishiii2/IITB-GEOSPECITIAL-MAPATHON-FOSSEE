import os
import requests
import time
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# Bounding box for India
LON_MIN, LAT_MIN = 68.0, 8.0
LON_MAX, LAT_MAX = 98.0, 38.0
STEP = 10.0  # NASA POWER API limit for regional

# The API limits NetCDF requests to 1 parameter at a time.
PARAMETERS = ["ALLSKY_SFC_SW_DWN", "WS50M"] 

def download_nasa_tiles():
    """Download Solar and Wind climatology data in 10x10 tiles to bypass API limits"""
    
    print("Downloading Solar and Wind data from NASA POWER API in tiles...")
    
    lons = np.arange(LON_MIN, LON_MAX, STEP)
    lats = np.arange(LAT_MIN, LAT_MAX, STEP)
    
    total_tiles = len(lons) * len(lats)
    
    for param in PARAMETERS:
        print(f"\n--- Downloading Parameter: {param} ---")
        current_tile = 1
        
        for lon in lons:
            for lat in lats:
                lon_max = min(lon + STEP, LON_MAX)
                lat_max = min(lat + STEP, LAT_MAX)
                
                tile_name = f"nasa_power_india_{param}_{lon}_{lat}_{lon_max}_{lat_max}.nc"
                tile_path = os.path.join(RAW_DIR, tile_name)
                
                if os.path.exists(tile_path):
                    print(f"[{current_tile}/{total_tiles}] Tile {tile_name} already exists. Skipping.")
                    current_tile += 1
                    continue
                    
                print(f"[{current_tile}/{total_tiles}] Downloading tile: Lon {lon} to {lon_max}, Lat {lat} to {lat_max}...")
                
                power_api_url = (
                    f"https://power.larc.nasa.gov/api/temporal/climatology/regional?"
                    f"parameters={param}&community=RE&"
                    f"longitude-min={lon}&latitude-min={lat}&"
                    f"longitude-max={lon_max}&latitude-max={lat_max}&format=NETCDF"
                )
                
                try:
                    time.sleep(2) # rate limiting
                    with requests.get(power_api_url, stream=True, timeout=120) as r:
                        if r.status_code != 200:
                            print(f"  -> Error: API returned status {r.status_code}. Response: {r.text}")
                            current_tile += 1
                            continue
                            
                        with open(tile_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    print(f"  -> Successfully saved {tile_name}")
                except requests.exceptions.RequestException as e:
                    print(f"  -> Error downloading tile {tile_name}: {e}")
                    
                current_tile += 1

    print("\nDownload process complete!")
    print("Tip: In 02_raster_preprocessing.py, you can load and stitch all these tiles together automatically using:")
    print("  import xarray as xr")
    print("  solar_ds = xr.open_mfdataset('data/raw/nasa_power_india_ALLSKY_SFC_SW_DWN_*.nc')")
    print("  wind_ds = xr.open_mfdataset('data/raw/nasa_power_india_WS50M_*.nc')")

if __name__ == "__main__":
    download_nasa_tiles()
