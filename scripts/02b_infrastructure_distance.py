import os
import numpy as np
import rasterio
from rasterio.features import rasterize
import geopandas as gpd
from scipy.ndimage import distance_transform_edt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")

INFRASTRUCTURE_GPKG = os.path.join(RAW_DIR, "india_power_infrastructure.gpkg")
SOLAR_TIF = os.path.join(PROCESSED_DIR, "india_solar_potential.tif")
DISTANCE_OUT = os.path.join(PROCESSED_DIR, "india_distance_to_grid.tif")

def calculate_euclidean_distance():
    print("--- PhD Upgrade: Logistical Constraints ---")
    print("Loading 45,000+ Power Lines and Substations...")
    
    try:
        # Load the power lines
        infra_gdf = gpd.read_file(INFRASTRUCTURE_GPKG)
        
        # Load the base grid from NASA Solar data
        with rasterio.open(SOLAR_TIF) as src:
            meta = src.meta.copy()
            transform = src.transform
            shape = src.shape
            
        print("Rasterizing the electrical grid onto the spatial matrix...")
        
        # Reproject infra to match raster if necessary (should already be EPSG:4326)
        if infra_gdf.crs != "EPSG:4326":
            infra_gdf = infra_gdf.to_crs("EPSG:4326")
            
        # Create a generator of geometries (value = 1)
        shapes = ((geom, 1) for geom in infra_gdf.geometry if geom is not None)
        
        # Rasterize: background is 0, power lines are 1
        binary_mask = rasterize(
            shapes,
            out_shape=shape,
            transform=transform,
            fill=0,
            dtype=np.uint8
        )
        
        print("Computing Euclidean Distance Transform across the subcontinent...")
        # EDT calculates distance from non-zero (power lines) to zero. 
        # So we want the power lines to be 0 and background to be 1.
        inverse_mask = (binary_mask == 0).astype(int)
        
        # Calculate pixel distance
        # We can multiply by pixel size (in degrees) to get degrees, or approx km.
        # ~111km per degree
        pixel_distance = distance_transform_edt(inverse_mask)
        pixel_size_x = abs(transform[0])
        distance_km = pixel_distance * pixel_size_x * 111.0 
        
        # Save to TIFF
        print(f"Saving Distance-to-Grid matrix to {DISTANCE_OUT}...")
        meta.update(dtype=rasterio.float32, nodata=-9999.0)
        with rasterio.open(DISTANCE_OUT, 'w', **meta) as dst:
            dst.write(distance_km.astype(np.float32), 1)
            
        print("Logistical features (Distance to Grid) successfully generated!")

    except Exception as e:
        print(f"Error computing distance: {e}")

if __name__ == "__main__":
    calculate_euclidean_distance()
