from flask import Blueprint, jsonify

suggestion_bp = Blueprint("suggestions", __name__)

# Dummy suggestion route for now (can be expanded later)
@suggestion_bp.route("/suggestions", methods=["GET"])
def get_suggestions():
    # Placeholder suggestions for testing
    sample_suggestions = [
        "Go for a walk 🚶",
        "Listen to music 🎧",
        "Call a friend 📞"  
    ]
    return jsonify({"suggestions": sample_suggestions})
