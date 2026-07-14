import os
import dask
import xarray as xr
import rioxarray

# Set up Dask for parallel processing of large rasters
from dask.distributed import Client

# Directory paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Target resolution and CRS for all rasters (EPSG:4326 for India, ~500m resolution)
TARGET_CRS = "EPSG:4326"
TARGET_RESOLUTION = 0.005  # approx 500m at equator

def process_raster(input_filename, output_filename, is_categorical=False):
    input_path = os.path.join(RAW_DIR, input_filename)
    output_path = os.path.join(PROCESSED_DIR, output_filename)
    
    if not os.path.exists(input_path):
        print(f"Warning: {input_filename} not found in {RAW_DIR}. Skipping.")
        return
        
    print(f"Processing {input_filename}...")
    
    # Open with chunking to prevent memory overload
    # Adjust chunks based on your RAM (e.g., 2048x2048)
    da = rioxarray.open_rasterio(input_path, chunks={'x': 2048, 'y': 2048})
    
    # Reproject to target CRS and Resolution
    resampling_method = 0 if is_categorical else 1 # 0=Nearest (for LULC), 1=Bilinear (for Solar/Wind)
    
    da_reprojected = da.rio.reproject(
        TARGET_CRS,
        resolution=TARGET_RESOLUTION,
        resampling=resampling_method
    )
    
    # Write to processed folder
    print(f"Saving to {output_filename}...")
    da_reprojected.rio.to_raster(output_path, tiled=True, windowed=True)
    print(f"Finished {output_filename}.")

if __name__ == "__main__":
    # Start Dask client to utilize all CPU cores
    client = Client()
    print("Dask client started. Dashboard link:", client.dashboard_link)
    
    # List of expected rasters to process
    # Note: These files must be manually placed in data/raw/ before running this script
    process_raster("solar_irradiance_raw.tif", "solar_aligned.tif", is_categorical=False)
    process_raster("wind_speed_raw.tif", "wind_aligned.tif", is_categorical=False)
    process_raster("dem_raw.tif", "dem_aligned.tif", is_categorical=False)
    process_raster("lulc_raw.tif", "lulc_aligned.tif", is_categorical=True)
    
    print("All raster preprocessing complete.")
