# server/models/mood_model.py
import joblib
import json
import os
import numpy as np

# Load model, MultiLabelBinarizer, and metadata
MODEL_PATH = os.path.join("ml", "mindmentor_model.joblib")
MLB_PATH = os.path.join("ml", "mindmentor_mlb.joblib")
META_PATH = os.path.join("ml", "model_metadata.json")

model = joblib.load(MODEL_PATH)
mlb = joblib.load(MLB_PATH)

with open(META_PATH, "r") as f:
    metadata = json.load(f)

FEATURES = metadata["features"]

def predict_mood(data: dict):
    try:
        # Extract feature values in the correct order
        input_values = [float(data[feature]) for feature in FEATURES]
        X = np.array([input_values])

        preds = model.predict(X)
        tags = mlb.inverse_transform(preds)[0]

        return {"tags": list(tags)}

    except Exception as e:
        print("🔥 Prediction error:", str(e))
        return {"tags": []}
