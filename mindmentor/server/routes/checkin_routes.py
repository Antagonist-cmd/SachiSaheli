from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
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
    return render_template("checkin.html")

@checkin_bp.route("/", methods=["POST"])
def handle_checkin_submission():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    # This is where we'll capture form data later
    data = request.form.to_dict()
    print("🧠 Submitted Check-in:", data)

    # For now, just redirect to check-in form
    return redirect(url_for("checkin.show_checkin_form"))

@checkin_bp.route("/mood", methods=["GET"])
def mood_form():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("mood_tracker.html")  # 🧠 reuse existing template!

@checkin_bp.route("/gratitude", methods=["GET", "POST"])
def gratitude_checkin():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        gratitude_text = request.form.get("gratitude_entry", "").strip()
        print("🙏 Gratitude Submitted:", gratitude_text)

        # TODO: Save it to Supabase later
        return redirect(url_for("checkin.gratitude_checkin"))

    return render_template("gratitude.html")

@checkin_bp.route("/energy", methods=["GET", "POST"])
def energy_checkin():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        energy = request.form.get("energy_level")
        motivation = request.form.get("motivation_level")
        print("⚡ Energy:", energy, "| 🚀 Motivation:", motivation)

        # TODO: Save to Supabase later
        return redirect(url_for("checkin.energy_checkin"))

    return render_template("energy_checkin.html")

@checkin_bp.route("/clarity", methods=["GET", "POST"])
def clarity_checkin():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        focus_level = request.form.get("focus_level")
        mental_fog = request.form.get("mental_fog")
        print("🧠 Focus Level:", focus_level, "| 🌫️ Mental Fog:", mental_fog)

        # TODO: Save to Supabase later
        return redirect(url_for("checkin.clarity_checkin"))

    return render_template("clarity_checkin.html")

@checkin_bp.route("/relaxation", methods=["GET", "POST"])
def relaxation_checkin():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        relaxation_level = request.form.get("relaxation_level")
        tension_level = request.form.get("tension_level")
        print("🧘 Relaxation:", relaxation_level, "| 💥 Tension:", tension_level)

        # TODO: Save to Supabase later
        return redirect(url_for("checkin.relaxation_checkin"))

    return render_template("relaxation_checkin.html")

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

@checkin_bp.route("/update-goal", methods=["POST"])
def update_goal():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    index = data.get("index")
    checked = data.get("checked")

    if index is None or checked is None:
        return jsonify({"error": "Invalid input"}), 400

    try:
        today = datetime.utcnow().date().isoformat()

        result = supabase.table("daily_goals") \
            .select("id, completed") \
            .eq("user_id", session["user_id"]) \
            .eq("date", today) \
            .single() \
            .execute()

        record = result.data
        
        if not record:
            return jsonify({"error": "No goal entry found for today"}), 404

        completed = record.get("completed", [])
        while len(completed) <= index:
            completed.append(False)

        completed[index] = checked

        supabase.table("daily_goals") \
            .update({"completed": completed}) \
            .eq("id", record["id"]) \
            .execute()

        return jsonify({"success": True})
    

    except Exception as e:
        print("⚠️ Goal update error:", str(e))
        return jsonify({"error": "Failed to update goal"}), 500
    

  

