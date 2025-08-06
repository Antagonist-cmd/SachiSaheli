# server/app.py
import os
import sys
from flask import Flask, render_template, redirect, session, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from utils.supabase_client import supabase  # Use single shared client
from datetime import datetime, timedelta
from collections import Counter
import random
from flask import jsonify
import json

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # store securely in prod
CORS(app)

# Import blueprints after app creation
from routes.auth_routes import auth_bp
from routes.mood_routes import mood_bp
from routes.suggestion_routes import suggestion_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(mood_bp, url_prefix="/api/mood")
app.register_blueprint(suggestion_bp, url_prefix="/api/suggestions")

# Page routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

from datetime import datetime

def calculate_streak(mood_entries):
    if not mood_entries:
        return 0

    streak = 0
    today = datetime.utcnow().date()
    prev_date = today

    for entry in mood_entries:
        ts = entry.get("timestamp")
        if not ts:
            continue

        # Parse timestamp safely if it's a string
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))

        entry_date = ts.date()

        if entry_date == prev_date:
            streak += 1
            prev_date = prev_date - timedelta(days=1)
        elif entry_date == prev_date - timedelta(days=1):
            streak += 1
            prev_date = entry_date
        else:
            break

    return streak


from flask import render_template, session, redirect, url_for
from datetime import datetime
import random
from collections import Counter

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    QUOTES = [
        "Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.",
        "Take a deep breath. You’re doing better than you think.",
        "Every emotion is valid. You’re allowed to feel what you feel.",
        "Small steps every day. That’s the secret to long-term progress.",
        "Rest is productive too. 💙",
        "You are more than your bad days.",
        "Keep going. Your future self is cheering for you.",
        "It’s okay to not be okay. Just don’t stay there."
    ]

    daily_quote = random.choice(QUOTES)

    try:
        result = supabase.table("mood_checkins") \
                         .select("*") \
                         .eq("user_id", session["user_id"]) \
                         .order("timestamp", desc=True) \
                         .execute()

        moods = result.data or []

        for mood in moods:
            # ✅ Fix timestamp
            if isinstance(mood.get("timestamp"), str):
                mood["timestamp"] = datetime.fromisoformat(mood["timestamp"].replace("Z", "+00:00"))

            ts = mood.get("timestamp")
            if not ts:
                continue

            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else ts
                mood["timestamp_obj"] = dt
                mood["timestamp_display"] = dt.strftime("%b %d, %Y at %I:%M %p")
                mood["timestamp_day"] = dt.strftime("%a")
            except Exception as e:
                print("⚠️ Timestamp parsing error:", ts, str(e))
                mood["timestamp_display"] = "Unknown"
                mood["timestamp_day"] = "N/A"
                mood["timestamp_obj"] = None

            # ✅ Fix suggestions list
            if isinstance(mood.get("suggestions"), str):
                mood["suggestions"] = mood["suggestions"].strip("{}").split(",")
            elif mood.get("suggestions") is None:
                mood["suggestions"] = []

            # ✅ Fix diagnosis_tags
            tags = mood.get("diagnosis_tags")
            if tags is None:
             mood["diagnosis_tags"] = []
            elif isinstance(tags, str):
                try:
        # Handle both JSON strings and comma-separated strings
                    mood["diagnosis_tags"] = json.loads(tags) if tags.startswith('[') else tags.split(',')
                except:
                    mood["diagnosis_tags"] = [tags]  # Fallback to single tag
            elif not isinstance(tags, list):
                mood["diagnosis_tags"] = [str(tags)]  # Convert non-list to list

        last_mood = moods[0] if moods else None
        mood_counts = Counter(tag for m in moods for tag in m.get("diagnosis_tags", []))
        mood_summary = [{"mood": mood, "count": count} for mood, count in mood_counts.items()]

        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning ☀️"
        elif hour < 18:
            greeting = "Good afternoon 🌞"
        else:
            greeting = "Good evening 🌙"

        return render_template(
            "dashboard.html",
            username=session.get("username", "User"),
            greeting=greeting,
            last_mood=last_mood,
            moods=moods,
            streak=calculate_streak(moods),
            mood_summary=mood_summary,
            quote=daily_quote
        )

    except Exception as e:
        print("Dashboard error:", str(e))
        return render_template("dashboard.html", username=session.get("username", "User"), moods=[], last_mood=None, streak=0)



@app.route('/delete_mood/<mood_id>', methods=['DELETE'])
def delete_mood(mood_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Delete from database
        supabase.table("mood_checkins") \
               .delete() \
               .eq("id", mood_id) \
               .eq("user_id", session["user_id"]) \
               .execute()
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Delete error: {str(e)}")
        return jsonify({"error": "Deletion failed"}), 500



@app.route("/mood-tracker")
def mood_tracker():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))
    return render_template("mood_tracker.html")

@app.route("/logout")
def logout_redirect():
    return redirect(url_for("auth.logout"))


if __name__ == "__main__":
    app.run(debug=True)

    #pandit