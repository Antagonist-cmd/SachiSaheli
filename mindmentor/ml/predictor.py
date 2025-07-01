# ml/predictor.py
import joblib
import numpy as np
import os
import json

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
        # Extract features in the correct order
        X = [float(input_data[feature]) for feature in FEATURES]
        X_scaled = np.array(X).reshape(1, -1)

        # Predict using pipeline
        y_pred = model.predict(X_scaled)
        tags = mlb.inverse_transform(y_pred)[0] if y_pred[0].any() else []

        return {"tags": tags}

    except Exception as e:
        print("🔥 Prediction error:", str(e))
        return {"tags": []}
print("model trained bcc!!!")