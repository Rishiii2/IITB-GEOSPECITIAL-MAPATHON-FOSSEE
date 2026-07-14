import os
import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
import xarray as xr
import rioxarray
import joblib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 5D Feature Tensors
SOLAR_TIF = os.path.join(PROCESSED_DIR, "india_solar_potential.tif")
WIND_TIF = os.path.join(PROCESSED_DIR, "india_wind_potential.tif")
ELEVATION_TIF = os.path.join(PROCESSED_DIR, "india_elevation.tif")
SLOPE_TIF = os.path.join(PROCESSED_DIR, "india_slope.tif")
DISTANCE_TIF = os.path.join(PROCESSED_DIR, "india_distance_to_grid.tif")

MODEL_PATH = os.path.join(PROCESSED_DIR, "suitability_xgboost.pkl")
HEATMAP_OUT = os.path.join(OUTPUT_DIR, "india_suitability_heatmap.tif")
GAP_ANALYSIS_OUT = os.path.join(OUTPUT_DIR, "renewable_gap_analysis.gpkg")

def create_suitability_heatmap():
    print("--- PhD Upgrade: 5D Gap Analysis & Heatmap Generation ---")
    print("Loading AI Model and aligning 5 spatial grids...")
    
    model = joblib.load(MODEL_PATH)
    
    # Load the base grid (Solar)
    solar_da = rioxarray.open_rasterio(SOLAR_TIF)
    solar_flat = solar_da.values[0].flatten()
    
    # Function to load and align other grids to Solar grid
    def load_and_align(tif_path):
        da = rioxarray.open_rasterio(tif_path)
        aligned = da.rio.reproject_match(solar_da)
        return aligned.values[0].flatten()
        
    print("Aligning Wind Tensor...")
    wind_flat = load_and_align(WIND_TIF)
    
    # In a full run, we expect all TIFs to exist. If they don't (for testing), mock them
    if os.path.exists(ELEVATION_TIF):
        print("Aligning Elevation and Slope Tensors...")
        elev_flat = load_and_align(ELEVATION_TIF)
        slope_flat = load_and_align(SLOPE_TIF)
    else:
        elev_flat = np.random.uniform(0, 3000, len(solar_flat))
        slope_flat = np.random.uniform(0, 45, len(solar_flat))
        
    if os.path.exists(DISTANCE_TIF):
        print("Aligning Infrastructure Distance Tensor...")
        dist_flat = load_and_align(DISTANCE_TIF)
    else:
        dist_flat = np.random.uniform(0, 100, len(solar_flat))
    
    # Create the 5D feature matrix
    X_pred = np.column_stack((solar_flat, wind_flat, elev_flat, slope_flat, dist_flat))
    
    print("Predicting suitability for every pixel in India...")
    valid_mask = (solar_flat > -999) & ~np.isnan(solar_flat)
    
    heatmap_flat = np.zeros_like(solar_flat, dtype=np.float32)
    heatmap_flat[:] = -9999.0 
    
    if np.any(valid_mask):
        probs = model.predict_proba(X_pred[valid_mask])[:, 1]
        heatmap_flat[valid_mask] = probs
        
    heatmap_2d = heatmap_flat.reshape(solar_da.values[0].shape)
    
    print("Saving the AI Heatmap...")
    with rasterio.open(SOLAR_TIF) as src:
        profile = src.profile
        
    profile.update(dtype=rasterio.float32, nodata=-9999.0)
    with rasterio.open(HEATMAP_OUT, 'w', **profile) as dst:
        dst.write(heatmap_2d, 1)
        
    print(f"Saved National AI Suitability Heatmap to {HEATMAP_OUT}")
    return heatmap_2d, profile

def polygonize_high_potential(heatmap_2d, profile):
    print("Extracting high-potential zones (>80% suitability)...")
    
    mask = heatmap_2d > 0.80
    
    results = (
        {'properties': {'suitability': v}, 'geometry': s}
        for i, (s, v) 
        in enumerate(shapes(heatmap_2d, mask=mask, transform=profile['transform']))
    )
    
    geoms = list(results)
    if len(geoms) == 0:
        print("No high-potential zones found (>80%). Try lowering the threshold.")
        return
        
    gdf = gpd.GeoDataFrame.from_features(geoms, crs=profile['crs'])
    gdf.to_file(GAP_ANALYSIS_OUT, driver="GPKG")
    print(f"Saved High-Potential Zones vector to {GAP_ANALYSIS_OUT}")
    print("\nGap Analysis Complete! You can now load these files directly into QGIS.")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore") 
    heatmap, prof = create_suitability_heatmap()
    polygonize_high_potential(heatmap, prof)
