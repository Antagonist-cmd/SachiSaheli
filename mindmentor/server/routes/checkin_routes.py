from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime

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
