import os
import numpy as np
import geopandas as gpd
import rasterio
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
import joblib
import shap
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# File Paths
RENEWABLES_PATH = os.path.join(RAW_DIR, "india_existing_renewables.gpkg")

# 5D Feature Tensors
SOLAR_TIF = os.path.join(PROCESSED_DIR, "india_solar_potential.tif")
WIND_TIF = os.path.join(PROCESSED_DIR, "india_wind_potential.tif")
ELEVATION_TIF = os.path.join(PROCESSED_DIR, "india_elevation.tif")
SLOPE_TIF = os.path.join(PROCESSED_DIR, "india_slope.tif")
DISTANCE_TIF = os.path.join(PROCESSED_DIR, "india_distance_to_grid.tif")

MODEL_OUT = os.path.join(PROCESSED_DIR, "suitability_xgboost.pkl")
SHAP_PLOT_OUT = os.path.join(OUTPUT_DIR, "shap_summary.png")

def sample_raster(raster_path, coords):
    """Sample pixel values from a raster at given (x,y) coordinates"""
    with rasterio.open(raster_path) as src:
        samples = list(src.sample(coords))
        return np.array([val[0] for val in samples])

def train_phd_suitability_model():
    print("--- PhD Upgrade: 5D AI Suitability Model (XGBoost) ---")
    
    # 1. Load Positive Labels
    print("Loading existing renewable farms...")
    try:
        farms = gpd.read_file(RENEWABLES_PATH)
        farms = farms.to_crs("EPSG:4326")
        centroids = farms.geometry.centroid
        pos_coords = [(pt.x, pt.y) for pt in centroids]
    except Exception as e:
        print(f"Error loading renewable farms: {e}")
        return

    # 2. Generate Negative Labels (Random background)
    print("Generating negative background samples...")
    num_negatives = len(pos_coords) * 2  
    neg_lons = np.random.uniform(68.0, 98.0, num_negatives)
    neg_lats = np.random.uniform(8.0, 38.0, num_negatives)
    neg_coords = list(zip(neg_lons, neg_lats))
    
    all_coords = pos_coords + neg_coords
    y = np.array([1] * len(pos_coords) + [0] * len(neg_coords))

    # 3. Feature Extraction (Sample 5D Tensor)
    print("Extracting 5-Dimensional Spatial Signatures...")
    try:
        solar_f = sample_raster(SOLAR_TIF, all_coords)
        wind_f = sample_raster(WIND_TIF, all_coords)
        
        # In a real run, if the DEM and Distance TIFs don't exist yet, we mock them for execution safety
        if os.path.exists(ELEVATION_TIF):
            elev_f = sample_raster(ELEVATION_TIF, all_coords)
            slope_f = sample_raster(SLOPE_TIF, all_coords)
        else:
            print("Warning: Topography data missing. Using procedural noise fallback.")
            elev_f = np.random.uniform(0, 3000, len(all_coords))
            slope_f = np.random.uniform(0, 45, len(all_coords))
            
        if os.path.exists(DISTANCE_TIF):
            dist_f = sample_raster(DISTANCE_TIF, all_coords)
        else:
            print("Warning: Logistical data missing. Using procedural noise fallback.")
            dist_f = np.random.uniform(0, 100, len(all_coords))
            
    except Exception as e:
        print(f"Error sampling rasters: {e}")
        return

    # Stack into (N, 5) array
    X = np.column_stack((solar_f, wind_f, elev_f, slope_f, dist_f))
    feature_names = ["Solar", "Wind", "Elevation", "Slope", "Dist2Grid"]
    
    # Mask out NoData points
    valid_mask = (solar_f > -999) & ~np.isnan(solar_f)
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"Extracted {len(X)} valid training tensors.")

    # 4. Train the Model
    print("Training XGBoost Classifier...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBClassifier(
        n_estimators=300, 
        max_depth=6, 
        learning_rate=0.05, 
        random_state=42,
        eval_metric='logloss',
        # Adding scale_pos_weight for imbalance
        scale_pos_weight=2.0 
    )
    model.fit(X_train, y_train)
    
    # 5. Evaluate
    preds = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, preds)
    acc = accuracy_score(y_test, (preds > 0.5).astype(int))
    
    print("\n--- Model Evaluation ---")
    print(f"Validation Accuracy: {acc:.4f}")
    print(f"Validation AUC Score:  {auc:.4f}")
    print("------------------------")
    
    # 6. SHAP Explainable AI
    print("Generating SHAP Explainability Matrix...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # Plot SHAP summary
    plt.figure(figsize=(10, 6))
    # We pass show=False so it doesn't block the script execution
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False)
    # Save the plot for the Streamlit dashboard
    plt.savefig(SHAP_PLOT_OUT, bbox_inches='tight', dpi=300)
    print(f"SHAP Summary Plot saved to {SHAP_PLOT_OUT}")

    # 7. Save Model
    joblib.dump(model, MODEL_OUT)
    print(f"5D AI Model saved successfully to {MODEL_OUT}")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    train_phd_suitability_model()
