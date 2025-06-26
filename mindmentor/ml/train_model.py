import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle

# Load the real dataset from file
data = pd.read_csv(r"C:\Users\jatin sharma\mindmentor\ml\mental_health_data.csv")

# Features and target
feature_cols = ["stress_level", "sleep_hours", "social_interaction", "appetite", "energy", "motivation", "concentration"]
X = data[feature_cols]
y = data["mental_state"]

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train model
model = RandomForestClassifier(random_state=42)
model.fit(X_scaled, y)

# Save updated scaler and model
with open(r"C:\Users\jatin sharma\mindmentor\ml\scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

with open(r"C:\Users\jatin sharma\mindmentor\ml\model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model trained using real dataset and saved successfully!")
