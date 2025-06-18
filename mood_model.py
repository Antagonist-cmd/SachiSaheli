import joblib
import numpy as np
import os

model_path = "D:/mindmentor/ml/model.pkl"
scaler_path = "D:/mindmentor/ml/scaler.pkl"


model = joblib.load(MODEL_PATH)
scaler = joblib.load(VECTORIZER_PATH)

def predict_mood(data):
    features = np.array([
        [
            float(data["stress_level"]),
            float(data["sleep_hours"]),
            float(data["social_interaction"]),
        ]
    ])

    scaled_features = scaler.transform(features)
    prediction = model.predict(scaled_features)[0]
    return prediction