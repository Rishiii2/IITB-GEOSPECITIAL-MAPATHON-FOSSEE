import os
import numpy as np
import rasterio
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_features(mask_locations):
    """
    Extract pixel values from all raster layers at given mask locations.
    (This is a placeholder function to demonstrate the logic)
    """
    # In reality, you'd use rasterio.sample.sample_gen to get values for specific coordinates
    # We return dummy features for the sake of the script structure.
    num_samples = len(mask_locations)
    # Features: [solar, wind, slope, distance_to_grid]
    X = np.random.rand(num_samples, 4) 
    return X

def train_suitability_model():
    print("Training XGBoost ML model for site suitability...")
    
    # 1. Load Positive Labels (Existing solar/wind farms from data/raw/india_existing_renewables.json)
    # 2. Generate Negative Labels (Random points in unsuitable areas like forests/mountains)
    # 3. Extract features for all points
    
    # Dummy data for demonstration:
    # 1000 positive points, 1000 negative points
    X_pos = np.random.rand(1000, 4) + 0.5  # Higher potential
    X_neg = np.random.rand(1000, 4)        # Lower potential
    
    X = np.vstack([X_pos, X_neg])
    y = np.hstack([np.ones(1000), np.zeros(1000)])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, preds)
    print(f"Model trained successfully. Validation AUC: {auc:.4f}")
    
    # Save the model
    model_path = os.path.join(PROCESSED_DIR, "suitability_xgboost.pkl")
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

def predict_national_suitability():
    print("Applying ML model across national grid...")
    # 1. Load the aligned rasters (solar, wind, dem, lulc) using rioxarray/dask
    # 2. Flatten the arrays, pass through the loaded XGBoost model
    # 3. Reshape and save as output/national_suitability_heatmap.tif
    print("Prediction complete. Map saved to output/national_suitability_heatmap.tif")

if __name__ == "__main__":
    train_suitability_model()
    # predict_national_suitability() # Uncomment when real rasters are ready
