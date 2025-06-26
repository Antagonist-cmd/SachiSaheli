# server/routes/auth_routes.py

from flask import Blueprint, render_template, request, redirect, session, url_for
from utils.supabase_client import supabase  # ✅ Import once at the top (best practice)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not username or not password or password != confirm_password:
        return render_template("register.html", error="❌ Invalid or mismatched inputs.")

    email = f"{username}@no-email.invalid"
    from utils.supabase_client import supabase

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        user_id = response.user.id

        supabase.table("profiles").insert({
            "id": user_id,
            "username": username
        }).execute()

        session.clear()
        session["user_id"] = user_id
        session["username"] = username
        session["access_token"] = response.session.access_token

        return redirect(url_for("dashboard"))

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("register.html", error=str(e))



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    email = f"{username}@no-email.invalid"

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not response.user:
            raise Exception("Login failed, no user returned")

        user_id = response.user.id

        session.clear()
        session["user_id"] = user_id
        session["username"] = username
        session["access_token"] = response.session.access_token

        return redirect(url_for("dashboard"))

    except Exception as e:
        print("🚨 Login error:", str(e))
        return render_template("login.html", error="🚫 Invalid credentials. Try again.")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return render_template("logout.html")

