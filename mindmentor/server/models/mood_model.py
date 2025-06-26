import pickle
import numpy as np

# Load model and scaler once, on import
with open("ml/model.pkl", "rb") as f:
    model = pickle.load(f)

with open("ml/scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

FEATURES = ["stress_level", "sleep_hours", "social_interaction", "appetite", "energy", "motivation", "concentration"]

def predict_mood(data: dict):
    # Extract features from input
    feature_values = [data.get(f, 0) for f in FEATURES]

    # Scale input features
    scaled = scaler.transform([feature_values])

    # Predict mood label
    prediction = model.predict(scaled)[0]

    # For simplicity, here you can have a fixed mapping of suggestions based on predicted mood
    suggestions_map = {
        "Happy": ["Keep up the great work!", "Maintain your routine!"],
        "Stressed": ["Try meditation", "Take short breaks"],
        "Depressed": ["Reach out to friends", "Consider professional help"],
        "Anxious": ["Practice breathing exercises", "Limit caffeine intake"],
        "Neutral": ["Stay active", "Engage in hobbies"]
    }
    suggestions = suggestions_map.get(prediction, [])

    return prediction, suggestions

