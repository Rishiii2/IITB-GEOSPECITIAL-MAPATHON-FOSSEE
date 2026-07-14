import os
import numpy as np
import geopandas as gpd
import rasterio
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
import joblib
from shapely.geometry import Point

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")

# File Paths
RENEWABLES_PATH = os.path.join(RAW_DIR, "india_existing_renewables.gpkg")
SOLAR_TIF = os.path.join(PROCESSED_DIR, "india_solar_potential.tif")
WIND_TIF = os.path.join(PROCESSED_DIR, "india_wind_potential.tif")
MODEL_OUT = os.path.join(PROCESSED_DIR, "suitability_xgboost.pkl")

def sample_raster(raster_path, coords):
    """Sample pixel values from a raster at given (x,y) coordinates"""
    with rasterio.open(raster_path) as src:
        # rasterio sample expects an iterable of (x, y) tuples
        samples = list(src.sample(coords))
        # The result is a list of arrays (one per band). We take the first band [0]
        return np.array([val[0] for val in samples])

def train_suitability_model():
    print("--- Training AI Suitability Model (XGBoost) ---")
    
    # 1. Load Positive Labels (Existing Solar/Wind Farms)
    print("Loading existing renewable farms from GeoPackage...")
    try:
        farms = gpd.read_file(RENEWABLES_PATH)
        # We need point coordinates to sample rasters. Use centroids of the polygons.
        # Reproject to EPSG:4326 to match our rasters
        farms = farms.to_crs("EPSG:4326")
        centroids = farms.geometry.centroid
        
        pos_coords = [(pt.x, pt.y) for pt in centroids]
        print(f"  -> Extracted {len(pos_coords)} positive farm locations.")
    except Exception as e:
        print(f"Error loading renewable farms: {e}")
        return

    # 2. Generate Negative Labels (Random background points)
    # To train the model, we need locations where farms ARE NOT located.
    # Bounding box of India: roughly 68.0E to 98.0E, 8.0N to 38.0N
    print("Generating negative background samples...")
    num_negatives = len(pos_coords) * 2  # 2:1 ratio for negatives
    neg_lons = np.random.uniform(68.0, 98.0, num_negatives)
    neg_lats = np.random.uniform(8.0, 38.0, num_negatives)
    neg_coords = list(zip(neg_lons, neg_lats))
    
    # Combine coordinates
    all_coords = pos_coords + neg_coords
    
    # Create labels: 1 for farms, 0 for background
    y = np.array([1] * len(pos_coords) + [0] * len(neg_coords))

    # 3. Feature Extraction (Sample Satellite Data)
    print("Sampling NASA Solar and Wind satellite data for all points...")
    try:
        solar_features = sample_raster(SOLAR_TIF, all_coords)
        wind_features = sample_raster(WIND_TIF, all_coords)
    except Exception as e:
        print(f"Error sampling rasters: {e}")
        return

    # Stack features into an (N, 2) array: [Solar, Wind]
    # (Note: In a full project, you'd also sample Distance to Grid and Slope here)
    X = np.column_stack((solar_features, wind_features))
    
    # Clean out any NoData points (where points fell in the ocean or outside raster bounds)
    # Assuming NASA NoData is highly negative or NaN
    valid_mask = (solar_features > -999) & (wind_features > -999) & ~np.isnan(solar_features) & ~np.isnan(wind_features)
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"Extracted {len(X)} valid training samples.")

    # 4. Train the Model
    print("Training XGBoost Classifier...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBClassifier(
        n_estimators=200, 
        max_depth=5, 
        learning_rate=0.05, 
        random_state=42,
        eval_metric='logloss'
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
    
    # 6. Save Model
    joblib.dump(model, MODEL_OUT)
    print(f"AI Model saved successfully to {MODEL_OUT}")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning) # Suppress geopandas centroid warning
    train_suitability_model()
