from flask import Blueprint, request, jsonify
import os
import pickle
import numpy as np

mood_bp = Blueprint("mood", __name__)
model_path = r"D:\mindmentor\ml\model.pkl"
scaler_path = r"D:\mindmentor\ml\scaler.pkl"

print("Loading model from:", model_path)
print("Loading scaler from:", scaler_path)

with open(model_path, "rb") as f:
    model = pickle.load(f)

with open(scaler_path, "rb") as f:
    scaler = pickle.load(f)

suggestions_dict = {
    "Depressed": [
        "Talk to a trusted friend or counselor 🗣️",
        "Try journaling your feelings 📝",
        "Do light exercises or go for a walk 🚶‍♂️"
    ],
    "Stressed": [
        "Practice deep breathing for 5 minutes 🌬️",
        "Take a short break from work or study 🧘",
        "Listen to calming music 🎵"
    ],
    "Anxious": [
        "Try grounding techniques like 5-4-3-2-1 🧠",
        "Reduce caffeine intake ☕",
        "Focus on slow, deep breaths 💨"
    ],
    "Happy": [
        "Keep doing what makes you feel good 😄",
        "Share your happiness with others ❤️",
        "Reflect on what's going well 🌟"
    ],
    "Neutral": [
        "Maybe try something new today 🌱",
        "Keep a gratitude journal 📔",
        "Reach out to a friend 🧑‍🤝‍🧑"
    ]
}

@mood_bp.route("/predict-and-save", methods=["POST"])
def predict_and_save():
    data = request.get_json()
    user_id = data.get("user_id")  # pass this from frontend after login

    # ... [scale + model.predict logic here] ...

    # Save to Supabase
    supabase.table("mood_checkins").insert({
        "user_id": user_id,
        "stress_level": data["stress_level"],
        "sleep_hours": data["sleep_hours"],
        "social_interaction": data["social_interaction"],
        "appetite": data["appetite"],
        "energy": data["energy"],
        "motivation": data["motivation"],
        "concentration": data["concentration"],
        "mental_state": prediction,
        "suggestions": suggestions
    }).execute()

    return jsonify({"mental_state": prediction, "suggestions": suggestions})

@mood_bp.route("/history/<user_id>", methods=["GET"])
def get_history(user_id):
    res = supabase.table("mood_checkins").select("*").eq("user_id", user_id).order("timestamp", desc=False).execute()
    return jsonify(res.data)


@mood_bp.route("/predict-mood", methods=["POST"])
def predict_mood():
    data = request.get_json()

    required_fields = ["stress_level", "sleep_hours", "social_interaction", "appetite",
                       "energy", "motivation", "concentration"]

    # Check if all required keys are present
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing one or more required fields"}), 400

    try:
        # Extract numerical features
        features = [
            float(data["stress_level"]),
            float(data["sleep_hours"]),
            float(data["social_interaction"]),
            float(data["appetite"]),
            float(data["energy"]),
            float(data["motivation"]),
            float(data["concentration"])
        ]

        features_array = np.array(features).reshape(1, -1)
        features_scaled = scaler.transform(features_array)

        prediction = model.predict(features_scaled)[0]
        suggestions = suggestions_dict.get(prediction, ["Take care of yourself 💚"])

        return jsonify({
            "mental_state": prediction,
            "suggestions": suggestions
        })

    except Exception as e:
        print("Prediction error:", e)
        return jsonify({"error": "Prediction failed"}), 500
