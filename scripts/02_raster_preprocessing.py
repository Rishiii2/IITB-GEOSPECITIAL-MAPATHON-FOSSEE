import os
import geopandas as gpd
import xarray as xr
import rioxarray
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def process_nasa_rasters():
    print("Stitching NASA POWER NetCDF tiles...")
    
    # Load and stitch Solar tiles
    solar_files = os.path.join(RAW_DIR, "nasa_power_india_ALLSKY_SFC_SW_DWN_*.nc")
    try:
        # open_mfdataset combines all matched files into one dataset
        ds_solar = xr.open_mfdataset(solar_files, combine='by_coords')
        
        # We need the 30-year climatology average (usually stored in the variable)
        # Assuming the variable is ALLSKY_SFC_SW_DWN and has dimensions (lat, lon)
        # NASA POWER climatology usually has a 'time' dimension of 13 (12 months + 1 annual average)
        # We'll take the annual average (which is usually the 13th index, or we can just mean across time)
        
        # For simplicity in this blueprint, let's take the mean across the time dimension
        solar_annual = ds_solar['ALLSKY_SFC_SW_DWN'].mean(dim='time', skipna=True)
        
        # Assign CRS (EPSG:4326 for standard lat/lon)
        solar_annual = solar_annual.rio.write_crs("epsg:4326")
        
        # Save to processed GeoTIFF
        solar_out = os.path.join(PROCESSED_DIR, "india_solar_potential.tif")
        solar_annual.rio.to_raster(solar_out)
        print(f"Saved National Solar Raster to {solar_out}")
        
    except Exception as e:
        print(f"Error processing Solar tiles: {e}")

    # Load and stitch Wind tiles
    wind_files = os.path.join(RAW_DIR, "nasa_power_india_WS50M_*.nc")
    try:
        ds_wind = xr.open_mfdataset(wind_files, combine='by_coords')
        wind_annual = ds_wind['WS50M'].mean(dim='time', skipna=True)
        wind_annual = wind_annual.rio.write_crs("epsg:4326")
        
        wind_out = os.path.join(PROCESSED_DIR, "india_wind_potential.tif")
        wind_annual.rio.to_raster(wind_out)
        print(f"Saved National Wind Raster to {wind_out}")
        
    except Exception as e:
        print(f"Error processing Wind tiles: {e}")

def prepare_infrastructure_data():
    """
    In a full pipeline, this function would:
    1. Load india_power_infrastructure.gpkg
    2. Rasterize the lines to match the NASA resolution
    3. Calculate Euclidean Distance to the nearest power line for every pixel
    """
    print("\nVector infrastructure data is ready in data/raw/india_power_infrastructure.gpkg")
    print("For the XGBoost model, we will calculate the distance from each pixel to the nearest power line.")
    print("(Distance transformation logic goes here - usually via scipy.ndimage.distance_transform_edt)")

if __name__ == "__main__":
    process_nasa_rasters()
    prepare_infrastructure_data()
    print("Raster preprocessing pipeline complete.")
