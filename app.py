import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, session
from flask_cors import CORS
from server.routes.mood_routes import mood_bp
from supabase import create_client
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv
from flask import session
from server.routes.auth_routes import auth_bp  # Adjust path if needed


load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY")  # in .env
app.register_blueprint(auth_bp, url_prefix="/api")

CORS(app)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Register blueprints
app.register_blueprint(mood_bp, url_prefix="/api")

# Home page
@app.route("/")
def home():
    return render_template("index.html")

# ✅ Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_pw = pbkdf2_sha256.hash(password)

        # Check if username exists
        existing = supabase.table("users1").select("*").eq("username", username).execute()
        if existing.data:
            return render_template("register.html", error="Username already exists 😬")

        # Insert user
        supabase.table("users1").insert({"username": username, "password": hashed_pw}).execute()
        session["user_id"] = user["user"]["id"]
        return redirect("/dashboard")

    return render_template("register.html")

# ✅ Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        result = supabase.table("users1").select("*").eq("username", username).execute()

        if result.data and pbkdf2_sha256.verify(password, result.data[0]["password"]):
            # Save the user ID or email to session
            session["user_id"] = result.data[0]["id"]
            session["username"] = result.data[0]["username"]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials 🚫")

    return render_template("login.html")

# ✅ Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ✅ Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    # Get user ID from session
    user_id = session["user_id"]

    # Fetch user-specific data from Supabase
    result = supabase.table("users1").select("*").eq("id", user_id).execute()
    
    if result.data:
        user_data = result.data[0]
        return render_template("dashboard.html", user=user_data)
    else:
        return "⚠️ User not found", 404

# Mood tracker page
@app.route("/mood-tracker")
def mood_tracker():
    return render_template("mood_tracker.html")

if __name__ == "__main__":
    app.run(debug=True)
