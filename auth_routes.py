from flask import Blueprint, request, jsonify, session
from supabase import Client
import os

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    user_response = supabase.auth.sign_up({"email": email, "password": password})
    print("Signup response:", user_response)

    if user_response.get("error"):
        return jsonify({"error": user_response["error"]["message"]}), 400

    user = user_response.get("user")
    if not user:
        return jsonify({"error": "Signup failed"}), 400

    supabase.table("users1").insert({
        "id": user["id"],
        "full_name": full_name
    }).execute()

    return jsonify({"user": user}), 200


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if "user" not in response:
        return jsonify({"error": response.get("error_description", "Login failed")}), 400

    session["user_id"] = response["user"]["id"]  # ✅ store unique user id

    return jsonify({"message": "Login successful", "user_id": response["user"]["id"]}), 200
