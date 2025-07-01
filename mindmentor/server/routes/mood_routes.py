import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.mood_model import predict_mood

from flask import Blueprint, request, jsonify, session
from utils.supabase_client import supabase
from datetime import datetime, timedelta
from flask import request
from models.mood_model import predict_mood
from flask import Blueprint, jsonify, request, session, redirect, url_for

mood_bp = Blueprint("mood", __name__)

def calculate_streak(mood_entries):
    """Returns the current streak count (consecutive days with check-ins)."""
    if not mood_entries:
        return 0

    streak = 0
    today = datetime.utcnow().date()

    for entry in mood_entries:
        entry_date = datetime.fromisoformat(entry["timestamp"]).date()

        # Check if the entry matches the expected streak day
        if entry_date == today - timedelta(days=streak):
            streak += 1
        else:
            break  # streak broken

    return streak




@mood_bp.route("/checkin", methods=["POST"])
def checkin():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        prediction_result = predict_mood(data)

        predicted_tags = prediction_result["tags"]

        checkin_data = {
            "user_id": session["user_id"],
            "age": data["age"],
            "gender": data["gender"],
            "stress_level": data["stress_level"],
            "sleep_hours": data["sleep_hours"],
            "sociability": data["sociability"],
            "anxiety": data["anxiety"],
            "emotional_stability": data["emotional_stability"],
            "self_esteem": data["self_esteem"],
            "motivation": data["motivation"],
            "eating_habits": data["eating_habits"],
            "diagnosis_tags": predicted_tags,
            "journal_entry": data.get("journal_entry"),
            "timestamp": datetime.now(datetime.UTC)
        }

        supabase.table("mood_checkins").insert(checkin_data).execute()

        return jsonify({"message": "Check-in saved ✅", "predicted_tags": predicted_tags})
    except Exception as e:
        print("🔥 Check-in error:", str(e))
        return jsonify({"error": "Failed to save mood check-in"}), 400






@mood_bp.route("/history", methods=["GET"])
def history():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    try:
        result = supabase.table("mood_checkins") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("timestamp", desc=True) \
            .execute()

        return jsonify(result.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mood_bp.route("/delete/<entry_id>", methods=["POST"])
def delete_mood_entry(entry_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Delete only if the entry belongs to the logged-in user
        supabase.table("mood_checkins") \
                .delete() \
                .eq("id", entry_id) \
                .eq("user_id", session["user_id"]) \
                .execute()
        return jsonify({"message": "Mood entry deleted ✅"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mood_bp.route("/predict", methods=["POST"])
def predict():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    try:
        prediction = predict_mood(data)
        return jsonify(prediction), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mood_bp.route("/journal", methods=["POST"])
def journal():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        entry = request.form.get("journal_entry", "").strip()

        if not entry:
            return jsonify({"error": "Empty journal entry"}), 400

        data = {
            "user_id": session["user_id"],
            "entry": entry
        }

        supabase.table("journals").insert(data).execute()

        return redirect(url_for("dashboard"))

    except Exception as e:
        print("📝 Journal save error:", str(e))
        return jsonify({"error": "Failed to save journal entry"}), 500
