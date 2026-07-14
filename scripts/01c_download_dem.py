import os
import xarray as xr
import rioxarray
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

ELEVATION_OUT = os.path.join(PROCESSED_DIR, "india_elevation.tif")
SLOPE_OUT = os.path.join(PROCESSED_DIR, "india_slope.tif")

def compute_slope(dem_array, cell_size_degrees):
    """
    Computes terrain slope in degrees from a DEM array using numpy gradients.
    """
    # 1 degree is roughly 111,320 meters at the equator
    # For a precise PhD-level model, you'd reproject to a metric CRS first, 
    # but for national scale, a static conversion factor is sufficient.
    cell_size_m = cell_size_degrees * 111320.0
    
    dy, dx = np.gradient(dem_array, cell_size_m, cell_size_m)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)
    
    return slope_deg

def fetch_dem_and_compute_slope():
    print("--- PhD Upgrade: Topographical Constraints ---")
    print("Fetching High-Res Digital Elevation Model (DEM) via OPeNDAP...")
    
    try:
        # We access the ETOPO1 1-arc-minute Global Relief Model from Columbia University's Stable OPeNDAP server
        # This completely bypasses downloading massive raw files, loading only our bounding box directly into RAM!
        url = "http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NGDC/.ETOPO1/.z_bedrock/dods"
        ds = xr.open_dataset(url)
        
        # Slicing the bounding box for India (Lon: 68E to 98E, Lat: 8N to 38N)
        print("Slicing the Indian subcontinent bounding box...")
        
        # Note: ETOPO1 lat/lon variables are 'X' and 'Y'
        india_dem = ds['z_bedrock'].sel(X=slice(68, 98), Y=slice(8, 38)).load()
        
        # Handle CRS mapping for rioxarray
        india_dem = india_dem.rename({"X": "x", "Y": "y"})
        india_dem.rio.write_crs("epsg:4326", inplace=True)
        
        # Save Elevation TIF
        print(f"Saving Elevation matrix to {ELEVATION_OUT}...")
        india_dem.rio.to_raster(ELEVATION_OUT)
        
        # Compute Slope
        print("Deriving terrain slope using 2D gradients...")
        resolution_deg = abs(india_dem.x.values[1] - india_dem.x.values[0])
        slope_array = compute_slope(india_dem.values, resolution_deg)
        
        # Create a new DataArray for Slope based on the DEM metadata
        india_slope = xr.DataArray(
            slope_array,
            coords=[india_dem.y, india_dem.x],
            dims=["y", "x"]
        )
        india_slope.rio.write_crs("epsg:4326", inplace=True)
        
        # Save Slope TIF
        print(f"Saving Slope matrix to {SLOPE_OUT}...")
        india_slope.rio.to_raster(SLOPE_OUT)
        
        print("Topographical features (Elevation & Slope) successfully generated!")
        
    except Exception as e:
        print(f"Error accessing OPeNDAP DEM: {e}")
        print("\nFallback: Could not connect to Columbia University Server.")
        print("In a production environment, ensure internet access or use a local DEM file.")

if __name__ == "__main__":
    fetch_dem_and_compute_slope()
