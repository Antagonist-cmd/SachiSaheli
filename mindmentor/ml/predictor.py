# ml/predictor.py
import joblib
import numpy as np
import os
import json
import pandas as pd  

# Load model, binarizer, and metadata
MODEL_PATH = os.path.join(os.path.dirname(__file__), "mindmentor_model.joblib")
MLB_PATH = os.path.join(os.path.dirname(__file__), "mindmentor_mlb.joblib")
META_PATH = os.path.join(os.path.dirname(__file__), "model_metadata.json")

model = joblib.load(MODEL_PATH)
mlb = joblib.load(MLB_PATH)

with open(META_PATH, "r") as f:
    metadata = json.load(f)

FEATURES = metadata["features"]



def predict_mood(input_data: dict):
    try:
        # ✅ Normalize gender input (string → int)
        if "gender" in input_data:
            gender_map = {"male": 0, "female": 1, "other": 2, "prefer-not-to-say": 3}
            input_data["gender"] = gender_map.get(str(input_data["gender"]).lower(), 3)

        # ✅ Extract and convert all features to float
        feature_values = [float(input_data[feature]) for feature in FEATURES]

        # ✅ Create a DataFrame with correct feature names
        X_df = pd.DataFrame([feature_values], columns=FEATURES)

        # ✅ Predict using trained pipeline (scaler is inside the pipeline if you saved it that way)
        y_pred = model.predict(X_df)
        tags = mlb.inverse_transform(y_pred)[0] if y_pred[0].any() else []

        return {"tags": tags}

    except Exception as e:
        print("🔥 Prediction error:", str(e))
        return {"tags": []}
