from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from utils.supabase_client import supabase
from supabase import create_client, Client
from datetime import date
from flask import flash 


checkin_bp = Blueprint("checkin", __name__, url_prefix="/check-in")

@checkin_bp.route("/", methods=["GET"])
def show_checkin_form():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Fetch today's goals
    today = datetime.now().date().isoformat()
    try:
        response = supabase.table("daily_goals") \
                           .select("*") \
                           .eq("user_id", session["user_id"]) \
                           .eq("date", today) \
                           .execute()
        goals_data = response.data[0] if response.data else None
    except Exception as e:
        print("⚠️ Failed to fetch daily goals:", str(e))
        goals_data = None

    return render_template("checkin.html", goals_data=goals_data)


@checkin_bp.route("/", methods=["POST"])
def handle_checkin_submission():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    data = request.form.to_dict(flat=False)  # get all checkbox values
    goals = data.get("goals", [])
    gratitude = request.json.get("gratitude") or request.form.get("gratitude")


    try:
        today = datetime.now().date().isoformat()
        supabase.table("daily_goals").insert({
            "user_id": session["user_id"],
            "goals": goals,
            "completed": [],
            "date": today,
            "gratitude": gratitude,
        }).execute()
        print("✅ Goals saved successfully.")
    except Exception as e:
        print("🚨 Failed to save daily goals:", str(e))

    return redirect(url_for("checkin.show_checkin_form"))

@checkin_bp.route("/mood", methods=["GET"])
def mood_form():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("mood_tracker.html")  # 🧠 reuse existing template!



@checkin_bp.route("/daily-goals", methods=["GET", "POST"])
def daily_goals():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    today_goals = []

    if request.method == "POST":
        goals = [
            request.form.get("goal1", "").strip(),
            request.form.get("goal2", "").strip(),
            request.form.get("goal3", "").strip(),
        ]
        goals = [g for g in goals if g]  # Remove empty ones
        completed = [False] * len(goals)

        try:
            supabase.table("daily_goals").insert({
                "user_id": session["user_id"],
                "goals": goals,
                "completed": completed,
                "date": date.today().isoformat()
            }).execute()
            flash("🎯 Goals saved successfully!")
        except Exception as e:
            print("🚨 Supabase Insert Error:", str(e))
            flash("❌ Failed to save goals.")

        return redirect(url_for("checkin.daily_goals"))

    # Fetch today's goals
    try:
        result = supabase.table("daily_goals") \
                         .select("goals, completed") \
                         .eq("user_id", session["user_id"]) \
                         .eq("date", date.today().isoformat()) \
                         .limit(1) \
                         .execute()
        data = result.data
        if data:
            today_goals = list(zip(data[0]["goals"], data[0]["completed"]))
    except Exception as e:
        print("⚠️ Fetching today's goals failed:", e)

    return render_template("daily_goals.html", today_goals=today_goals)

@checkin_bp.route("/api/goals/save", methods=["POST"])
def update_goal():  # or whatever your "update goal" route is called
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = session["user_id"]
        data = request.get_json()
        completed = data.get("completed", [])

        today = datetime.utcnow().date()

        # Update only the completed field
        supabase.table("daily_goals") \
            .update({"completed": completed}) \
            .eq("user_id", user_id) \
            .eq("date", today.isoformat()) \
            .execute()

        return jsonify({"message": "✅ Goals updated successfully!"})

    except Exception as e:
        print("❌ Error updating goals:", e)
        return jsonify({"error": "Something went wrong."}), 500

@checkin_bp.route("/update-goals", methods=["POST"])
def update_goal_status():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    completed = request.form.getlist("completed_goals")
    today = datetime.now().date().isoformat()

    try:
        # Fetch existing goal row
        response = supabase.table("daily_goals") \
                           .select("id") \
                           .eq("user_id", session["user_id"]) \
                           .eq("date", today) \
                           .execute()

        if response.data:
            goal_id = response.data[0]["id"]
            supabase.table("daily_goals").update({
                "completed": completed
            }).eq("id", goal_id).execute()

            print("✅ Goal status updated.")
    except Exception as e:
        print("🚨 Failed to update goal status:", str(e))

    return redirect(url_for("checkin.show_checkin_form"))

@checkin_bp.route("/calendar", methods=["GET"])
def calendar_view():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    try:
        result = supabase.table("mood_checkins") \
                         .select("timestamp, diagnosis_tags") \
                         .eq("user_id", session["user_id"]) \
                         .execute()
        checkins = result.data or []

        # Group mood check-ins by date
        mood_by_date = {}
        for entry in checkins:
            ts = entry.get("timestamp")
            if ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                tags = entry.get("diagnosis_tags") or []
                mood_by_date[date_str] = tags[0] if tags else "Unknown"


        return render_template("calendar.html", mood_by_date=mood_by_date)
    
    except Exception as e:
        print("📛 Calendar error:", str(e))
        return render_template("calendar.html", mood_by_date={})

# 📁 Route: Gratitude Archive (For Highlight Display)
@checkin_bp.route("/gratitude-archive")
def gratitude_archive():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    try:
        result = supabase.table("gratitude_entries") \
            .select("gratitude_text, timestamp") \
            .eq("user_id", session["user_id"]) \
            .not_.is_("gratitude_text", None) \
            .order("timestamp", desc=True) \
            .execute()

        entries = [
            {
                "text": g["gratitude_text"],
                "timestamp": datetime.fromisoformat(g["timestamp"].replace("Z", "+00:00")).strftime("%b %d, %Y"),
            }
            for g in result.data
            if g.get("gratitude_text")
        ]

        return render_template("gratitude_archive.html", entries=entries)

    except Exception as e:
        print("❌ Gratitude Archive Error:", str(e))
        return render_template("gratitude_archive.html", entries=[])



# 📁 Route: Gratitude Journal (For Main Journal View)
@checkin_bp.route("/gratitude-journal")
def gratitude_journal():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    try:
        result = supabase.table("gratitude_entries") \
                         .select("*") \
                         .eq("user_id", session["user_id"]) \
                         .order("created_at", desc=True) \
                         .execute()

        entries = result.data or []
        return render_template("gratitude.html", entries=entries)

    except Exception as e:
        print("❌ Gratitude Journal Error:", str(e))
        return render_template("gratitude.html", entries=[])


@checkin_bp.route("/gratitude", methods=["POST"])
def save_gratitude():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    gratitude_text = request.form.get("gratitude")

    try:
        response = supabase.table("gratitude_entries").insert({
            "user_id": session["user_id"],
            "gratitude_text": gratitude_text
        }).execute()

        print("✅ Gratitude saved:", response)
        return redirect(url_for("checkin.gratitude_journal"))

    except Exception as e:
        print("🔥 Gratitude Save Error:", str(e))
        return redirect(url_for("checkin.gratitude_journal"))
