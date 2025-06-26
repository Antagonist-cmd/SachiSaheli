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

def get_earned_badges(mood_entries):
    badges = []
    if not mood_entries:
        return badges

    # Badge 1: 📓 Reflective Soul (3+ journal entries)
    journal_count = sum(1 for m in mood_entries if m.get("journal_entry"))
    if journal_count >= 3:
        badges.append("📓 Reflective Soul")

    # Badge 2: 🔁 Consistency Hero (7-day check-in streak)
    if calculate_streak(mood_entries) >= 7:
        badges.append("🔁 Consistency Hero")

    # Badge 3: 💪 Resilience Champ (5+ check-ins in the last 7 days)
    today = datetime.now(datetime.UTC).date()
    last_7_days = [m for m in mood_entries if "timestamp_obj" in m and m["timestamp_obj"].date() >= today - timedelta(days=6)]
    if len(last_7_days) >= 5:
        badges.append("💪 Resilience Champ")

    # Badge 4: 🧘 Zen Master (3+ Neutral days in a row)
    neutral_streak = 0
    for m in mood_entries:
        if m.get("mental_state") == "Neutral":
            neutral_streak += 1
            if neutral_streak >= 3:
                badges.append("🧘 Zen Master")
                break
        else:
            neutral_streak = 0

    return badges

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
        
    
        # Convert timestamp string to datetime object if needed
        for mood in moods:

    # Convert timestamp
            if isinstance(mood["timestamp"], str):
                mood["timestamp"] = datetime.fromisoformat(mood["timestamp"].replace("Z", "+00:00"))
        
    # ✅ Force suggestions to be a list
            if isinstance(mood.get("suggestions"), str):
                mood["suggestions"] = mood["suggestions"].strip("{}").split(",")
            elif mood.get("suggestions") is None:
                mood["suggestions"] = []

            ts=mood.get("timestamps")
            if not ts:
                continue
            try:
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                else:
                    dt = ts  # Already a datetime object

                mood["timestamp_obj"] = dt
                mood["timestamp_display"] = dt.strftime("%b %d, %Y at %I:%M %p")
                mood["timestamp_day"] = dt.strftime("%a")

            except Exception as e:
                print("⚠️ Timestamp parsing error:", ts, str(e))
                mood["timestamp_display"] = "Unknown"
                mood["timestamp_day"] = "N/A"
                mood["timestamp_obj"] = None

            # Parse suggestions into list if needed
            if isinstance(mood.get("suggestions"), str):
                mood["suggestions"] = mood["suggestions"].strip("{}").split(",")
            elif mood.get("suggestions") is None:
                mood["suggestions"] = []
        
        
        last_mood = moods[0] if moods else None
        
        mood_counts = Counter(m["mental_state"] for m in moods if m.get("mental_state"))

# Convert to a list of (mood, count) tuples
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
            streak = calculate_streak(moods),
            mood_summary=mood_summary,
            quote=daily_quote
        )
    
        return render_template(
            "dashboard.html",
            username=session.get("username", "User"),
            last_mood=last_mood,
            moods=moods,
            streak=streak
        )
    

    except Exception as e:
        print("Dashboard error:", str(e))
        return render_template("dashboard.html", username=session.get("username", "User"), moods=[], last_mood=None, streak=0)






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
