# server/routes/mood_routes.py
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
from utils.supabase_client import supabase
import sys
import os

# Add path to access the ml module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ml.predictor import predict_mood

mood_bp = Blueprint("mood", __name__)

@mood_bp.route("/checkin", methods=["POST"])
def checkin():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        
        print(f"Received data: {data}")

        gender_map = {
            "male": "male",
            "female": "female", 
            "other": "other",
            "prefer-not-to-say": "prefer-not-to-say"
        }
        gender_val = gender_map.get(data.get("gender", "prefer-not-to-say"), "prefer-not-to-say")

        # FIXED CODE:
        prediction_data = {
            "age": int(data.get("age", 19)),
            "stress_level": float(data.get("stress_level", 5)),
            "sleep_hours": float(data.get("sleep_hours", 7)),
            "sociability": float(data.get("sociability", 5)),
            "anxiety": float(data.get("anxiety", 5)),
            "emotional_stability": float(data.get("emotional_stability", 5)),
            "self_esteem": float(data.get("self_esteem", 5)),
            "motivation": float(data.get("motivation", 5)),
            "eating_habits": float(data.get("eating_habits", 5))
        }

        
        print(f"Prediction data: {prediction_data}")

        prediction_result = predict_mood(prediction_data)
        
        # Ensure all required fields exist with safe defaults
        predicted_tags = prediction_result.get("tags", [])
        confidence = prediction_result.get("confidence", "low")
        direct_actions = prediction_result.get("direct_actions", {
            "immediate_steps": [],
            "daily_habits": [],
            "weekly_goals": [],
            "lifestyle_changes": []
        })

        checkin_data = {
            "user_id": session["user_id"],
            "age": int(data.get("age", 19)),
            "gender": gender_val,
            "stress_level": float(data.get("stress_level", 5)),
            "sleep_hours": float(data.get("sleep_hours", 7)),
            "sociability": float(data.get("sociability", 5)),
            "anxiety": float(data.get("anxiety", 5)),
            "emotional_stability": float(data.get("emotional_stability", 5)),
            "self_esteem": float(data.get("self_esteem", 5)),
            "motivation": float(data.get("motivation", 5)),
            "eating_habits": float(data.get("eating_habits", 5)),
            "substance_abuse": float(data.get("substance_abuse", 0)),
            "diagnosis_tags": predicted_tags,
            "journal_entry": data.get("journal_entry", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        result = supabase.table("mood_checkins").insert(checkin_data).execute()

        return jsonify({
            "message": "Check-in saved successfully", 
            "predicted_tags": predicted_tags,
            "confidence": confidence,
            "direct_actions": direct_actions,
            "checkin_id": result.data[0]["id"] if result.data else None
        })

    except Exception as e:
        print(f"Check-in error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to save mood check-in"}), 500

@mood_bp.route("/action-plan/<checkin_id>", methods=["GET"])
def get_action_plan(checkin_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result = supabase.table("mood_checkins") \
            .select("*") \
            .eq("id", checkin_id) \
            .eq("user_id", session["user_id"]) \
            .execute()

        if not result.data:
            return jsonify({"error": "Check-in not found"}), 404

        checkin = result.data[0]
        
        input_data = {
            "age": checkin["age"],
            "stress_level": checkin["stress_level"],
            "sleep_hours": checkin["sleep_hours"],
            "sociability": checkin["sociability"],
            "anxiety": checkin["anxiety"],
            "emotional_stability": checkin["emotional_stability"],
            "self_esteem": checkin["self_esteem"],
            "motivation": checkin["motivation"],
            "eating_habits": checkin["eating_habits"]
        }

        prediction = predict_mood(input_data)
        
        return jsonify({
            "tags": checkin["diagnosis_tags"],
            "confidence": checkin.get("confidence_score", "moderate"),
            "direct_actions": prediction.get("direct_actions", {}),
            "timestamp": checkin["timestamp"]
        })

    except Exception as e:
        print(f"Action plan error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to get action plan"}), 500

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

        mood_history = result.data or []
        
        for mood in mood_history:
            if not mood.get("diagnosis_tags"):
                mood["diagnosis_tags"] = []
            
            mood["mental_state"] = mood["diagnosis_tags"][0] if mood["diagnosis_tags"] else "Unknown"
            mood["suggestions"] = mood["diagnosis_tags"]
            
            if isinstance(mood["timestamp"], str):
                dt = datetime.fromisoformat(mood["timestamp"].replace("Z", "+00:00"))
                mood["timestamp_display"] = dt.strftime("%b %d, %Y at %I:%M %p")
                mood["timestamp_day"] = dt.strftime("%a")

        return jsonify(mood_history), 200
        
    except Exception as e:
        print(f"History fetch error: {str(e)}")
        return jsonify({"error": "Failed to fetch mood history"}), 500

@mood_bp.route("/delete/<entry_id>", methods=["POST", "DELETE"])
def delete_mood_entry(entry_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result = supabase.table("mood_checkins") \
                .delete() \
                .eq("id", entry_id) \
                .eq("user_id", session["user_id"]) \
                .execute()
        
        if result.data:
            return jsonify({"message": "Mood entry deleted successfully"})
        else:
            return jsonify({"error": "Entry not found or unauthorized"}), 404
            
    except Exception as e:
        print(f"Delete error: {str(e)}")
        return jsonify({"error": "Failed to delete mood entry"}), 500

@mood_bp.route("/predict", methods=["POST"])
def predict():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        
        prediction_data = {
            "age": data.get("age", 19),
            "stress_level": data.get("stress_level", 5),
            "sleep_hours": data.get("sleep_hours", 7),
            "sociability": data.get("sociability", 5),
            "anxiety": data.get("anxiety", 5),
            "emotional_stability": data.get("emotional_stability", 5),
            "self_esteem": data.get("self_esteem", 5),
            "motivation": data.get("motivation", 5),
            "eating_habits": data.get("eating_habits", 5)
        }
        
        prediction = predict_mood(prediction_data)
        return jsonify(prediction), 200
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify({"error": "Prediction failed"}), 500

@mood_bp.route("/stats", methods=["GET"])
def get_stats():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result = supabase.table("mood_checkins") \
            .select("*") \
            .eq("user_id", session["user_id"]) \
            .order("timestamp", desc=True) \
            .execute()

        moods = result.data or []
        
        from collections import Counter
        
        intervention_counts = Counter(mood.get("intervention_level", "monitoring") for mood in moods)
        confidence_counts = Counter(mood.get("confidence_score", "moderate") for mood in moods)
        
        tag_counts = Counter()
        for mood in moods:
            if mood.get("diagnosis_tags"):
                for tag in mood["diagnosis_tags"]:
                    tag_counts[tag] += 1
        
        recent_trends = []
        if len(moods) >= 5:
            recent_moods = moods[:5]
            stress_trend = [m.get("stress_level", 5) for m in recent_moods]
            anxiety_trend = [m.get("anxiety", 5) for m in recent_moods]
            sleep_trend = [m.get("sleep_hours", 7) for m in recent_moods]
            
            recent_trends = {
                "stress_average": sum(stress_trend) / len(stress_trend),
                "anxiety_average": sum(anxiety_trend) / len(anxiety_trend),
                "sleep_average": sum(sleep_trend) / len(sleep_trend)
            }
        
        return jsonify({
            "total_checkins": len(moods),
            "confidence_distribution": dict(confidence_counts),
            "top_conditions": dict(tag_counts.most_common(5)),
            "recent_trends": recent_trends,
            "last_checkin": moods[0]["timestamp"] if moods else None
        })
        
    except Exception as e:
        print(f"Stats error: {str(e)}")
        return jsonify({"error": "Failed to fetch statistics"}), 500
