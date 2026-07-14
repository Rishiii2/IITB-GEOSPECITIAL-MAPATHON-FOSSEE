import os
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# NASA POWER API - Regional Climatology (30-year average)
# Bounding box for India: long_min=68.1, lat_min=8.0, long_max=97.4, lat_max=37.1
# Parameters:
# ALLSKY_SFC_SW_DWN = All Sky Surface Shortwave Downward Irradiance (Solar)
# WS50M = Wind Speed at 50 Meters
POWER_API_URL = (
    "https://power.larc.nasa.gov/api/temporal/climatology/regional?"
    "parameters=ALLSKY_SFC_SW_DWN,WS50M&"
    "community=RE&"
    "longitude-min=68.1&latitude-min=8.0&longitude-max=97.4&latitude-max=37.1&"
    "format=NETCDF"
)

NASA_NETCDF_PATH = os.path.join(RAW_DIR, "nasa_power_india_climate.nc")

def download_nasa_power_data():
    """Download Solar and Wind climatology data for India from NASA POWER"""
    if os.path.exists(NASA_NETCDF_PATH):
        print(f"File {NASA_NETCDF_PATH} already exists. Skipping download.")
        return
        
    print("Downloading Solar and Wind data from NASA POWER API...")
    print("Requesting: ", POWER_API_URL)
    
    try:
        with requests.get(POWER_API_URL, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(NASA_NETCDF_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Download complete! Saved to {NASA_NETCDF_PATH}")
        print("Note: You can read this file directly into xarray in 02_raster_preprocessing.py")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading NASA POWER data: {e}")

if __name__ == "__main__":
    download_nasa_power_data()
    print("Raster data pipeline complete.")
    print("For higher resolution data (like ISRO Bhuvan LULC or SRTM DEM), please download them manually from their respective portals and place them in data/raw/.")
