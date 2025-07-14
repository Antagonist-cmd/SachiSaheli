# server/app.py
import os
import sys
from flask import Flask, render_template, redirect, session, url_for, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from utils.supabase_client import supabase  # Use single shared client
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
import random
from dateutil import parser

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
from routes.help_routes import help_bp
from routes.checkin_routes import checkin_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(mood_bp, url_prefix="/api/mood")
app.register_blueprint(suggestion_bp, url_prefix="/api/suggestions")
app.register_blueprint(help_bp)
app.register_blueprint(checkin_bp)

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

def calculate_streak(mood_entries):
    """Calculate mood check-in streak with backward compatibility"""
    if not mood_entries:
        return 0
    
    streak = 0
    # Use timezone-aware datetime for consistency
    today = datetime.now(timezone.utc).date()
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

def derive_simple_mood(tags):
    """Derive simple mood categories from diagnosis tags"""
    if not tags:
        return "Neutral"
    
    tags = [t.lower().strip() for t in tags]
    
    if any(t in tags for t in ["depression", "suicidal thoughts"]):
        return "Very Sad"
    if any(t in tags for t in ["anxiety", "burnout", "insomnia"]):
        return "Sad"
    if any(t in tags for t in ["motivated", "balanced"]):
        return "Happy"
    if any(t in tags for t in ["very happy", "gratitude"]):
        return "Very Happy"
    
    return "Neutral"

def process_mood_data(moods):
    """Process mood data with enhanced analytics"""
    weekly_tags = Counter()
    weekday_mood_map = {}
    insights = []
    weekly_tag_distribution = defaultdict(lambda: Counter())
    
    for mood in moods:
        # Fix timestamp handling
        ts = mood.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            mood["timestamp"] = ts
        
        if not ts:
            continue
        
        dt = ts
        week_key = dt.strftime("%G-W%V")  # e.g., 2025-W27
        weekday = dt.strftime("%a")
        
        # Set timestamp display properties
        mood["timestamp_obj"] = dt
        mood["timestamp_display"] = dt.strftime("%b %d, %Y at %I:%M %p")
        mood["timestamp_day"] = weekday
        
        # Handle diagnosis_tags properly (backward compatibility)
        if isinstance(mood.get("diagnosis_tags"), list):
            mood["diagnosis_tags"] = mood["diagnosis_tags"]
        elif isinstance(mood.get("diagnosis_tags"), str):
            mood["diagnosis_tags"] = mood["diagnosis_tags"].strip("{}").split(",")
        elif mood.get("diagnosis_tags") is None:
            mood["diagnosis_tags"] = []
        
        # Set mental_state for backward compatibility
        mood["mental_state"] = mood["diagnosis_tags"][0] if mood["diagnosis_tags"] else "Unknown"
        
        # Clean suggestions handling
        if isinstance(mood.get("suggestions"), str):
            mood["suggestions"] = mood["suggestions"].strip("{}").split(",")
        elif mood.get("suggestions") is None:
            mood["suggestions"] = mood.get("diagnosis_tags", [])  # Fallback to diagnosis_tags
        
        # Process tags for analytics
        tags = mood.get("diagnosis_tags", [])
        for tag in tags:
            clean_tag = tag.strip()
            weekly_tags[clean_tag.lower()] += 1
            weekly_tag_distribution[week_key][clean_tag] += 1
        
        # Derive simple mood
        mood["simple_mood"] = derive_simple_mood(tags)
        weekday_mood_map[weekday] = mood["simple_mood"]
    
    # Generate insights
    if weekly_tags.get("anxiety", 0) >= 3:
        insights.append("You've been anxious 3+ times this week. Try cutting down caffeine or taking screen breaks.")
    if weekly_tags.get("low motivation", 0) >= 2:
        insights.append("Low motivation seems common – maybe a quick nature walk or journaling could help.")
    if weekly_tags.get("burnout", 0) >= 2:
        insights.append("Burnout alerts! Take a breather. Schedule light activities to recharge.")
    
    # Prep data for stacked bar chart
    weekly_mood_data = []
    for week, tag_counts in sorted(weekly_tag_distribution.items()):
        entry = {"week": week}
        entry.update(tag_counts)
        weekly_mood_data.append(entry)
    
    return {
        'insights': insights,
        'weekly_mood_trend': weekday_mood_map,
        'weekly_mood_data': weekly_mood_data,
        'weekly_tags': weekly_tags
    }

@app.route("/dashboard")
def dashboard():
    # Check authentication with fallback to multiple redirect targets
    if "user_id" not in session:
        # Try both auth blueprint and direct login page
        try:
            return redirect(url_for("auth.login"))
        except:
            return redirect(url_for("login_page"))
    
    # Enhanced quotes with emojis
    QUOTES = [
        "Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.",
        "Take a deep breath. You're doing better than you think.",
        "Every emotion is valid. You're allowed to feel what you feel.",
        "Small steps every day. That's the secret to long-term progress.",
        "Rest is productive too. 💙",
        "You are more than your bad days.",
        "Keep going. Your future self is cheering for you.",
        "It's okay to not be okay. Just don't stay there."
    ]
    daily_quote = random.choice(QUOTES)
    
    try:
        # Fetch mood data
        result = supabase.table("mood_checkins") \
                         .select("*") \
                         .eq("user_id", session["user_id"]) \
                         .order("timestamp", desc=True) \
                         .execute()
        moods = result.data or []
        
        # Process mood data with enhanced analytics
        analytics = process_mood_data(moods)
        
        # Get last mood
        last_mood = moods[0] if moods else None
        
        # Calculate mood summary (using both diagnosis_tags and mental_state)
        mood_counts = Counter()
        for m in moods:
            # Count by diagnosis_tags
            for tag in m.get("diagnosis_tags", []):
                mood_counts[tag] += 1
            # Also count by mental_state for backward compatibility
            if m.get("mental_state") and m.get("mental_state") != "Unknown":
                mood_counts[m["mental_state"]] += 1
        
        mood_summary = [{"mood": mood, "count": count} for mood, count in mood_counts.items()]
        
        # Enhanced greeting with emojis
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
            quote=daily_quote,
            insights=analytics['insights'],
            weekly_mood_trend=analytics['weekly_mood_trend'],
            weekly_mood_data=analytics['weekly_mood_data']
        )
        
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        # Return safe fallback with all required template variables
        return render_template(
            "dashboard.html",
            username=session.get("username", "User"),
            greeting="Hello",
            moods=[],
            last_mood=None,
            streak=0,
            mood_summary=[],
            quote=daily_quote,
            insights=[],
            weekly_mood_trend={},
            weekly_mood_data=[]
        )

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
        # Try both auth blueprint and direct login page
        try:
            return redirect(url_for("auth.login"))
        except:
            return redirect(url_for("login_page"))
    
    return render_template("mood_tracker.html")

@app.route("/logout")
def logout_redirect():
    return redirect(url_for("auth.logout"))

if __name__ == "__main__":
    app.run(debug=True)