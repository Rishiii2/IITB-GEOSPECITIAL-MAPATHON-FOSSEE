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

SOLAR_TIF = os.path.join(PROCESSED_DIR, "india_solar_potential.tif")
WIND_TIF = os.path.join(PROCESSED_DIR, "india_wind_potential.tif")
MODEL_PATH = os.path.join(PROCESSED_DIR, "suitability_xgboost.pkl")
HEATMAP_OUT = os.path.join(OUTPUT_DIR, "india_suitability_heatmap.tif")
GAP_ANALYSIS_OUT = os.path.join(OUTPUT_DIR, "renewable_gap_analysis.gpkg")

def create_suitability_heatmap():
    print("--- Running Gap Analysis & Heatmap Generation ---")
    print("Loading AI Model and aligning satellite grids...")
    
    model = joblib.load(MODEL_PATH)
    
    # Use rioxarray to seamlessly load and align the rasters
    # (NASA Solar and Wind datasets have slightly different native grid resolutions!)
    solar_da = rioxarray.open_rasterio(SOLAR_TIF)
    wind_da = rioxarray.open_rasterio(WIND_TIF)
    
    print("Reprojecting and resampling Wind data to perfectly match the Solar grid...")
    wind_aligned = wind_da.rio.reproject_match(solar_da)
    
    solar_data = solar_da.values[0]
    wind_data = wind_aligned.values[0]
    
    # Flatten the 2D arrays to 1D for the model
    solar_flat = solar_data.flatten()
    wind_flat = wind_data.flatten()
    
    # Create the feature matrix
    X_pred = np.column_stack((solar_flat, wind_flat))
    
    # Predict probabilities (Suitability score from 0.0 to 1.0)
    print("Predicting suitability for every pixel in India...")
    # Handle NaNs / NoData before predicting
    valid_mask = (solar_flat > -999) & (wind_flat > -999) & ~np.isnan(solar_flat) & ~np.isnan(wind_flat)
    
    heatmap_flat = np.zeros_like(solar_flat, dtype=np.float32)
    heatmap_flat[:] = -9999.0 # NoData value
    
    # Only predict on valid land pixels
    if np.any(valid_mask):
        probs = model.predict_proba(X_pred[valid_mask])[:, 1]
        heatmap_flat[valid_mask] = probs
        
    # Reshape back to 2D
    heatmap_2d = heatmap_flat.reshape(solar_data.shape)
    
    # Save the heatmap TIFF using rasterio
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
    
    # Create a binary mask of highly suitable areas
    mask = heatmap_2d > 0.80
    
    # Polygonize the mask using rasterio
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
    
    # Save to GeoPackage for QGIS viewing
    gdf.to_file(GAP_ANALYSIS_OUT, driver="GPKG")
    print(f"Saved High-Potential Zones vector to {GAP_ANALYSIS_OUT}")
    print("\nGap Analysis Complete! You can now load these files directly into QGIS.")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore") # Suppress spatial merge warnings
    heatmap, prof = create_suitability_heatmap()
    polygonize_high_potential(heatmap, prof)
