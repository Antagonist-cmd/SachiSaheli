# ml/ai_suggestions.py
import google.generativeai as genai
import json

# Your Gemini API key
GEMINI_API_KEY = "AIzaSyD3En9sNvx0jNv4yVCE_d1iV6WNGqV6DLc"
genai.configure(api_key=GEMINI_API_KEY)

def generate_ai_suggestions(predicted_tags, input_data, journal_entry=""):
    """Generate personalized AI suggestions based on predicted conditions and user data"""
    
    try:
        # Create the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Build context prompt
        prompt = f"""You are a mental health AI assistant. A person has completed a mood assessment and you need to provide personalized, actionable suggestions.

**Assessment Results:**
- Predicted conditions: {', '.join(predicted_tags)}
- Age: {input_data.get('age', 'Unknown')}
- Stress level: {input_data.get('stress_level', 'Unknown')}/10
- Sleep hours: {input_data.get('sleep_hours', 'Unknown')} hours
- Anxiety level: {input_data.get('anxiety', 'Unknown')}/10
- Emotional stability: {input_data.get('emotional_stability', 'Unknown')}/10
- Self-esteem: {input_data.get('self_esteem', 'Unknown')}/10
- Motivation: {input_data.get('motivation', 'Unknown')}/10
- Social interaction: {input_data.get('sociability', 'Unknown')}/10
- Eating habits: {input_data.get('eating_habits', 'Unknown')}/10

**Personal reflection:** "{journal_entry}"

Return ONLY valid JSON in this exact format:
{{"immediate_steps": ["step1", "step2"], "daily_habits": ["habit1", "habit2"], "weekly_goals": ["goal1", "goal2"], "lifestyle_changes": ["change1", "change2"]}}"""

        # Generate AI response
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Simple cleanup - remove markdown if present
        response_text = response_text.replace("``````", "").strip()
        
        # Parse JSON
        suggestions = json.loads(response_text)
        
        # Validate structure
        required_keys = ["immediate_steps", "daily_habits", "weekly_goals", "lifestyle_changes"]
        for key in required_keys:
            if key not in suggestions or not isinstance(suggestions[key], list):
                suggestions[key] = [f"Focus on managing {', '.join(predicted_tags).lower()}"]
        
        return suggestions
        
    except Exception as e:
        print(f"AI suggestion generation error: {str(e)}")
        return {
            "immediate_steps": [
                "Take 5 deep breaths and ground yourself",
                f"Acknowledge that you're working through {', '.join(predicted_tags).lower()}"
            ],
            "daily_habits": [
                "Set aside 10 minutes each morning for self-reflection",
                "Practice one small act of self-care daily"
            ],
            "weekly_goals": [
                "Connect with someone who supports your wellbeing",
                "Try one new coping strategy this week"
            ],
            "lifestyle_changes": [
                "Build a routine that prioritizes your mental health",
                "Consider professional support if symptoms permits"
            ]
        }
