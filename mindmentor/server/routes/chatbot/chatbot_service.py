# routes/chatbot/chatbot_service.py
import google.generativeai as genai
import json
from datetime import datetime
from typing import List, Dict, Optional
from .prompts import MENTAL_HEALTH_SYSTEM_PROMPT, CONVERSATION_STARTERS

class MindMentorGeminiChatbot:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        """
        Initialize the MindMentor Gemini AI Chatbot
        
        Args:
            api_key: Google Gemini API key
            model: Gemini model to use (gemini-1.5-flash, gemini-1.5-pro)
        """
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(
            model_name=model,
            system_instruction=MENTAL_HEALTH_SYSTEM_PROMPT
        )
        self.max_context_length = 15  # Keep last 15 messages for context
        
        # Configure safety settings for mental health discussions
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"  # Allow mental health discussions
            }
        ]
        
        # Configure generation parameters for empathetic responses
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 1000,
        }
        
    def generate_response(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Generate AI response using Gemini for user message
        
        Args:
            user_message: User's input message
            conversation_history: Previous conversation messages
            
        Returns:
            Dict with response, conversation_id, timestamp
        """
        try:
            # Start a chat session with history
            chat = self.model.start_chat(history=self._prepare_history(conversation_history))
            
            # Generate response
            response = chat.send_message(
                user_message,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            ai_response = response.text.strip()
            
            return {
                "success": True,
                "response": ai_response,
                "timestamp": datetime.now().isoformat(),
                "model": self.model_name,
                "tokens_used": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }
            
        except Exception as e:
            print(f"❌ Gemini Chatbot error: {str(e)}")
            
            # Handle specific Gemini errors
            error_message = str(e).lower()
            if "safety" in error_message or "blocked" in error_message:
                fallback_response = "I understand you're going through something difficult. While I want to help, I think it would be best to speak with a mental health professional who can provide the specialized support you need. Would you like me to share some resources?"
            elif "quota" in error_message or "limit" in error_message:
                fallback_response = "I'm currently experiencing high demand. Please try again in a moment, or consider reaching out to a mental health professional if you need immediate support."
            else:
                fallback_response = "I'm having some technical difficulties right now. Please try again, or reach out to a mental health professional if you need immediate support."
            
            return {
                "success": False,
                "response": fallback_response,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "model": self.model_name
            }
    
    def _prepare_history(self, conversation_history: List[Dict] = None) -> List[Dict]:
        """Prepare conversation history for Gemini format"""
        if not conversation_history:
            return []
        
        # Convert to Gemini format and limit context
        recent_history = conversation_history[-self.max_context_length:]
        gemini_history = []
        
        for msg in recent_history:
            role = "user" if msg.get("role") == "user" else "model"
            gemini_history.append({
                "role": role,
                "parts": [msg.get("content", "")]
            })
        
        return gemini_history
    
    def get_conversation_starters(self) -> List[str]:
        """Get suggested conversation starters"""
        return CONVERSATION_STARTERS
    
    def analyze_user_mood(self, message: str) -> Dict:
        """Analyze potential mood indicators in user message"""
        mood_keywords = {
            "anxious": ["anxious", "anxiety", "worried", "nervous", "panic", "stressed", "overwhelming"],
            "depressed": ["sad", "depressed", "hopeless", "empty", "worthless", "tired", "exhausted"],
            "angry": ["angry", "frustrated", "mad", "irritated", "annoyed", "furious"],
            "happy": ["happy", "good", "great", "excited", "joy", "positive", "amazing"],
            "confused": ["confused", "lost", "stuck", "don't know", "uncertain", "unclear"],
            "lonely": ["lonely", "alone", "isolated", "abandoned", "disconnected"],
            "overwhelmed": ["overwhelmed", "too much", "can't handle", "drowning", "suffocating"]
        }
        
        message_lower = message.lower()
        detected_moods = []
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_moods.append(mood)
        
        # Enhanced crisis detection
        crisis_phrases = [
            "suicide", "kill myself", "end it all", "can't go on", "want to die",
            "no point living", "better off dead", "hurt myself", "self harm",
            "ending everything", "can't take it anymore"
        ]
        
        return {
            "detected_moods": detected_moods,
            "needs_priority_response": any(phrase in message_lower for phrase in crisis_phrases),
            "mood_intensity": len(detected_moods)  # Higher number = more intense emotional state
        }

    def generate_mood_summary(self, message: str) -> Dict:
        """Generate a quick mood summary using Gemini"""
        try:
            prompt = f"""
            Analyze this message for emotional indicators: "{message}"
            
            Respond with ONLY a JSON object containing:
            {{
                "primary_emotion": "main emotion detected",
                "intensity": "low/medium/high",
                "support_needed": "brief description of what support might help"
            }}
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.3, "max_output_tokens": 200}
            )
            
            return json.loads(response.text.strip())
            
        except Exception as e:
            print(f"❌ Mood analysis error: {str(e)}")
            return {
                "primary_emotion": "mixed",
                "intensity": "unknown", 
                "support_needed": "general emotional support"
            }
