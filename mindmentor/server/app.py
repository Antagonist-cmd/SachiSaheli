# server/app.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template
from flask_cors import CORS
from server.routes.mood_routes import mood_bp
# from server.routes.auth_routes import auth_bp
# from server.routes.suggestion_routes import suggestion_bp

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Register blueprints
app.register_blueprint(mood_bp, url_prefix="/api")
# app.register_blueprint(auth_bp, url_prefix="/api")
# app.register_blueprint(suggestion_bp, url_prefix="/api")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/mood-tracker")
def mood_tracker():
    return render_template("mood_tracker.html")

if __name__ == "__main__":
    app.run(debug=True)
