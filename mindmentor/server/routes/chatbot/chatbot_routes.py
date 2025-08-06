# routes/chatbot/chatbot_routes.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from .chatbot_service import MindMentorGeminiChatbot
from .prompts import CRISIS_RESOURCES, COPING_TECHNIQUES
import os
from datetime import datetime

# Create chatbot blueprint
chatbot_bp = Blueprint('chatbot', __name__)

# Initialize Gemini chatbot service
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

if GEMINI_API_KEY:
    chatbot_service = MindMentorGeminiChatbot(GEMINI_API_KEY, GEMINI_MODEL)
    print(f"🤖 Using Google Gemini {GEMINI_MODEL} for chatbot")
else:
    print("❌ GEMINI_API_KEY not found in environment variables")
    chatbot_service = None

@chatbot_bp.route('/chat')
def chat_page():
    """Render the main chatbot interface"""
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    
    if not chatbot_service:
        return render_template('error.html', 
                             message="Chatbot service is currently unavailable. Please check configuration.")
    
    return render_template('chatbot.html', 
                         username=session.get('username', 'User'),
                         conversation_starters=chatbot_service.get_conversation_starters())

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat_api():
    """Handle chat API requests with Gemini"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not chatbot_service:
        return jsonify({
            "success": False,
            "error": "Chatbot service unavailable",
            "fallback_message": "The AI chatbot is currently unavailable. Please try again later."
        }), 503
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if len(user_message) > 2000:  # Reasonable limit
            return jsonify({"error": "Message too long. Please keep under 2000 characters."}), 400
        
        # Get conversation history from session
        conversation_key = f"gemini_chat_history_{session['user_id']}"
        conversation_history = session.get(conversation_key, [])
        
        # Analyze user mood for potential crisis detection
        mood_analysis = chatbot_service.analyze_user_mood(user_message)
        
        # Generate enhanced mood summary for high-intensity situations
        mood_summary = None
        if mood_analysis.get("mood_intensity", 0) > 2:
            mood_summary = chatbot_service.generate_mood_summary(user_message)
        
        print(f"🧠 Mood analysis: {mood_analysis}")
        if mood_summary:
            print(f"📊 Mood summary: {mood_summary}")
        
        # Generate Gemini AI response
        ai_response = chatbot_service.generate_response(
            user_message, 
            conversation_history
        )
        
        if ai_response["success"]:
            # Update conversation history
            conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            conversation_history.append({
                "role": "assistant", 
                "content": ai_response["response"],
                "timestamp": ai_response["timestamp"],
                "model": ai_response["model"]
            })
            
            # Keep only last 30 messages to prevent session bloat
            if len(conversation_history) > 30:
                conversation_history = conversation_history[-30:]
            
            session[conversation_key] = conversation_history
            
            # Prepare response data
            response_data = {
                "success": True,
                "message": ai_response["response"],
                "timestamp": ai_response["timestamp"],
                "model": ai_response.get("model", "gemini"),
                "tokens_used": ai_response.get("tokens_used", 0)
            }
            
            # Add crisis resources for high-priority situations
            if mood_analysis["needs_priority_response"]:
                response_data["crisis_resources"] = CRISIS_RESOURCES
                response_data["priority"] = "high"
                print("🚨 Crisis situation detected - adding emergency resources")
            
            # Add relevant coping techniques based on detected moods
            if mood_analysis["detected_moods"]:
                response_data["coping_suggestions"] = []
                added_suggestions = set()  # Prevent duplicates
                
                for mood in mood_analysis["detected_moods"]:
                    if mood in COPING_TECHNIQUES:
                        for suggestion in COPING_TECHNIQUES[mood][:2]:  # Max 2 per mood
                            if suggestion not in added_suggestions:
                                response_data["coping_suggestions"].append(suggestion)
                                added_suggestions.add(suggestion)
                
                # Limit total suggestions
                response_data["coping_suggestions"] = response_data["coping_suggestions"][:4]
            
            # Add mood summary for intense emotional states
            if mood_summary:
                response_data["mood_analysis"] = mood_summary
            
            return jsonify(response_data)
        
        else:
            return jsonify({
                "success": False,
                "error": ai_response.get("error", "Failed to generate response"),
                "fallback_message": ai_response["response"],
                "model": ai_response.get("model", "gemini")
            }), 500
            
    except Exception as e:
        print(f"❌ Chat API error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "fallback_message": "I'm experiencing some technical difficulties. Please try again in a moment, or reach out to a mental health professional if you need immediate support."
        }), 500

@chatbot_bp.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear Gemini chat history"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    conversation_key = f"gemini_chat_history_{session['user_id']}"
    session.pop(conversation_key, None)
    
    return jsonify({"success": True, "message": "Chat history cleared", "model": "gemini"})

@chatbot_bp.route('/api/chat/export', methods=['GET'])
def export_chat():
    """Export Gemini chat history"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    conversation_key = f"gemini_chat_history_{session['user_id']}"
    conversation_history = session.get(conversation_key, [])
    
    return jsonify({
        "success": True,
        "conversation": conversation_history,
        "exported_at": datetime.now().isoformat(),
        "total_messages": len(conversation_history),
        "ai_model": "Google Gemini",
        "export_version": "1.0"
    })

@chatbot_bp.route('/api/chat/suggestions')
def get_suggestions():
    """Get conversation starter suggestions"""
    if not chatbot_service:
        return jsonify({"error": "Service unavailable"}), 503
    
    return jsonify({
        "success": True,
        "suggestions": chatbot_service.get_conversation_starters(),
        "model": "gemini"
    })

@chatbot_bp.route('/api/chat/health')
def chatbot_health():
    """Health check endpoint for chatbot service"""
    if not chatbot_service:
        return jsonify({
            "status": "unhealthy",
            "error": "Gemini API key not configured"
        }), 503
    
    return jsonify({
        "status": "healthy",
        "model": GEMINI_MODEL,
        "provider": "Google Gemini",
        "version": "1.0"
    })
