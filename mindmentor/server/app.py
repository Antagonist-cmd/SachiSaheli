# server/app.py
import os
import sys
from flask import Flask, render_template, redirect, session, url_for, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from utils.supabase_client import supabase  # Use single shared client
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
import random
from dateutil import parser

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://bapvnpcabwpsmxxrmrrj.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJhcHZucGNhYndwc214eHJtcnJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzNDk1ODMsImV4cCI6MjA2NTkyNTU4M30.Hq8WAOz_9WL68wjjxaEJfvONQRP_YN7CAB3Q32J6sSY')
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
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


TAG_MEANINGS = {
    "Anxiety": "A feeling of worry, nervousness, or unease, typically about an imminent event.",
    "Burnout": "Physical and mental exhaustion often caused by prolonged stress or overwork.",
    "Depression": "A persistent feeling of sadness and loss of interest that affects how you feel and act.",
    "Healthy": "A positive state of mental well-being with good emotional regulation.",
    "Hopelessness": "A feeling or state of despair; lack of hope.",
    "Isolation Risk": "Tendency to withdraw socially, which can impact overall mental health.",
    "Low Self-Esteem": "Viewing yourself in a negative or critical way; lack of confidence.",
    "Mood Swings": "Rapid, often extreme fluctuations in one's emotional state.",
    "Stable": "Consistently balanced mood and emotions.",
    "Stress": "State of mental or emotional strain from challenging circumstances.",
    # ...add other tags as needed
}
TAG_SUGGESTIONS = {
    "Anxiety": [
        "Practice deep breathing or grounding exercises.",
        "Limit caffeine and screen time.",
        "Try guided meditation or mindfulness apps."
    ],
    "Burnout": [
        "Schedule regular breaks throughout your day.",
        "Consider light activities like walking or stretching.",
        "Reach out to someone you trust about how you are feeling."
    ],
    "Depression": [
        "Spend time in sunlight or nature when possible.",
        "Keep a gratitude journal.",
        "Talk to a mental health professional if feelings persist."
    ],
    "Healthy": [
        "Maintain your positive routines!",
        "Keep connecting with friends or loved ones.",
        "Celebrate small wins and self-care moments."
    ],
    "Hopelessness": [
        "Talk to a trusted friend or counselor about your feelings.",
        "Reflect on small positive changes each day.",
        "Remember that feelings are temporary and support is available."
    ],
    # ...add more suggestions as needed
}


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
    if not tags:
        return "Neutral"

    # Normalize tags for consistent matching
    normalized_tags = [t.lower().strip().replace("_", " ") for t in tags]

    # 🎯 Define mood categories
    very_sad_tags = {
        "suicidal thoughts", "depression", "hopelessness",
        "severe depression", "major depression"
    }

    sad_tags = {
        "anxiety", "burnout", "insomnia", "stress", "low motivation",
        "low self-esteem", "emotional instability", "isolation",
        "social withdrawal", "substance abuse", "disordered eating",
        "mood swings", "apathy", "addiction", "substance dependence"
    }

    happy_tags = {
        "balanced", "calm", "focused", "healthy", "motivated",
        "stable", "good mood", "positive", "content", "relaxed"
    }

    very_happy_tags = {
        "very happy", "gratitude", "joy", "excited", "elated",
        "euphoric", "blissful", "thriving", "excellent"
    }

    if any(tag in normalized_tags for tag in very_sad_tags):
        return "Very Sad"
    if any(tag in normalized_tags for tag in sad_tags):
        return "Sad"
    if any(tag in normalized_tags for tag in very_happy_tags):
        return "Very Happy"
    if any(tag in normalized_tags for tag in happy_tags):
        return "Happy"

    return "Neutral"




def process_mood_data(moods):
    from collections import Counter, defaultdict
    from datetime import datetime

    weekly_tags = Counter()
    weekday_mood_map = {}
    insights = []
    weekly_tag_distribution = defaultdict(lambda: Counter())

    for mood in moods:
        ts = mood.get("timestamp")

        # ✅ Handle ISO string and datetime conversion
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                mood["timestamp"] = ts
            except Exception as e:
                print("Invalid timestamp:", ts)
                continue

        if not ts:
            continue

        dt = ts
        week_key = dt.strftime("%G-W%V")
        weekday = dt.strftime("%a")

        mood["timestamp_obj"] = dt
        mood["timestamp_display"] = dt.strftime("%b %d, %Y at %I:%M %p")
        mood["timestamp_day"] = weekday

        # ✅ Safely parse raw diagnosis_tags without modifying the original
        raw_tags = mood.get("diagnosis_tags")
        if isinstance(raw_tags, list):
            tags = raw_tags
        elif isinstance(raw_tags, str):
            try:
                tags = json.loads(raw_tags) if raw_tags.strip().startswith("[") else raw_tags.strip("{}").split(",")
                tags = [t.strip() for t in tags if t]
            except:
                tags = []
        else:
            tags = []

        # ✅ Set original (unmodified) tags back — needed by streak & summaries
        mood["diagnosis_tags"] = tags

        # ✅ Normalize only for internal mood calculations
        normalized_tags = [t.lower().strip().replace("_", " ") for t in tags]

        # ✅ Default mental state
        mood["mental_state"] = normalized_tags[0] if normalized_tags else "Unknown"

        # ✅ Clean suggestions
        raw_suggestions = mood.get("suggestions")
        if isinstance(raw_suggestions, str):
            suggestions = [s.strip() for s in raw_suggestions.strip("{}").split(",") if s.strip()]
        elif isinstance(raw_suggestions, list):
            suggestions = raw_suggestions
        else:
            suggestions = tags  # fallback

        mood["suggestions"] = suggestions

        # Count tags for weekly charts
        for tag in normalized_tags:
            weekly_tags[tag] += 1
            weekly_tag_distribution[week_key][tag] += 1

        # Derive simplified mood for graphs
        mood["diagnosis_tags"] = tags  # original format
        mood["mental_state"] = normalized_tags[0] if normalized_tags else "Unknown"
        mood["simple_mood"] = derive_simple_mood(normalized_tags)
        mood["timestamp_day"] = weekday
        weekday_mood_map[weekday] = mood["simple_mood"]

    # ✅ Weekly mental health insights
    if weekly_tags.get("anxiety", 0) >= 3:
        insights.append("You've been anxious 3+ times this week. Try cutting down caffeine or taking screen breaks.")
    if weekly_tags.get("low motivation", 0) >= 2:
        insights.append("Low motivation seems common – maybe a quick nature walk or journaling could help.")
    if weekly_tags.get("burnout", 0) >= 2:
        insights.append("Burnout alerts! Take a breather. Schedule light activities to recharge.")

    # ✅ Format data for chart
    weekly_mood_data = []
    for week, tag_counts in sorted(weekly_tag_distribution.items()):
        entry = {"week": week}
        entry.update({tag.title(): count for tag, count in tag_counts.items()})
        weekly_mood_data.append(entry)

    return {
        'insights': insights,
        'weekly_mood_trend': weekday_mood_map,
        'weekly_mood_data': weekly_mood_data,
        'weekly_tags': weekly_tags
    }

def process_mood_data_for_chart(moods, time_range='30'):
    """Process mood data specifically for chart visualization - keeps your existing logic intact"""
    from datetime import datetime, timedelta
    
    if not moods:
        return {
            'labels': [],
            'data': [],
            'moods': [],
            'interpolated': []
        }
    
    # Filter by time range if specified
    filtered_moods = moods
    if time_range != 'all':
        try:
            days = int(time_range)
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_moods = [
                mood for mood in moods 
                if datetime.fromisoformat(mood.get('timestamp', '').replace("Z", "+00:00")) >= cutoff_date
            ]
        except:
            filtered_moods = moods[:30]  # Fallback to last 30 entries
    
    # Process moods using your existing logic
    processed_moods = []
    for mood in filtered_moods:
        ts = mood.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except:
                continue
        
        # Use your existing tag processing
        raw_tags = mood.get("diagnosis_tags", [])
        if isinstance(raw_tags, list):
            tags = raw_tags
        elif isinstance(raw_tags, str):
            try:
                tags = json.loads(raw_tags) if raw_tags.strip().startswith("[") else raw_tags.strip("{}").split(",")
                tags = [t.strip() for t in tags if t]
            except:
                tags = []
        else:
            tags = []
        
        # Use your existing derive_simple_mood function
        normalized_tags = [t.lower().strip().replace("_", " ") for t in tags]
        simple_mood = derive_simple_mood(normalized_tags)
        
        processed_moods.append({
            **mood,
            'timestamp_obj': ts,
            'date_key': ts.strftime("%Y-%m-%d"),
            'simple_mood': simple_mood,
            'diagnosis_tags': tags
        })
    
    # Sort by timestamp (oldest first for chart)
    processed_moods.sort(key=lambda x: x['timestamp_obj'])
    
    # Group by date - take latest mood per day
    daily_moods = {}
    for mood in processed_moods:
        date_key = mood['date_key']
        if date_key not in daily_moods or mood['timestamp_obj'] > daily_moods[date_key]['timestamp_obj']:
            daily_moods[date_key] = mood
    
    # Convert to chart format
    labels = []
    data = []
    mood_entries = []
    
    for date_key in sorted(daily_moods.keys()):
        mood = daily_moods[date_key]
        date_obj = datetime.strptime(date_key, "%Y-%m-%d")
        label = date_obj.strftime("%b %d")
        
        labels.append(label)
        data.append(convert_mood_to_score(mood['simple_mood']))
        mood_entries.append(mood)
    
    return {
        'labels': labels,
        'data': data,
        'moods': mood_entries,
        'interpolated': [False] * len(labels)
    }

def convert_mood_to_score(mood):
    """Convert simple mood to numeric score for chart"""
    mood_scores = {
        "Very Sad": 1,
        "Sad": 2,
        "Neutral": 3,
        "Happy": 4,
        "Very Happy": 5
    }
    return mood_scores.get(mood, 3)


@app.route("/api/mood/chart-data")
def get_chart_data():
    """AJAX endpoint for dynamic chart updates - minimal addition"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    time_range = request.args.get('range', '30')
    
    try:
        # Use same query logic as your dashboard
        result = supabase.table("mood_checkins") \
                         .select("*") \
                         .eq("user_id", session["user_id"]) \
                         .order("timestamp", desc=True) \
                         .execute()
        moods = result.data or []
        
        # Process for chart using new helper function
        chart_data = process_mood_data_for_chart(moods, time_range)
        
        return jsonify({
            "success": True,
            "data": chart_data,
            "count": len(chart_data['moods']),
            "range": time_range
        })
        
    except Exception as e:
        print(f"Chart data error: {str(e)}")
        return jsonify({"error": "Failed to fetch chart data"}), 500


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
    
    # 🔧 NEW: Get time range parameter for chart filtering
    time_range = request.args.get('range', '30')
    
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
            weekly_mood_data=analytics['weekly_mood_data'],
            time_range=time_range  # 🔧 NEW: Pass time range to template
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
            weekly_mood_data=[],
            time_range=time_range  # 🔧 NEW: Pass time range to template
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
    # You may fetch previous diagnosis tags from session, DB, or elsewhere if you want
    # For now simply pass the mappings so you can use them in the template

    return render_template(
        "mood_tracker.html",
        tag_meanings=TAG_MEANINGS,
        tag_suggestions=TAG_SUGGESTIONS,
    )


@app.route("/logout")
def logout_redirect():
    return redirect(url_for("auth.logout"))

if __name__ == "__main__":
    app.run(debug=True)