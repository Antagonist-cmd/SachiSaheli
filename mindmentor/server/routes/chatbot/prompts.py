# routes/chatbot/prompts.py

MENTAL_HEALTH_SYSTEM_PROMPT = """
You are MindMentor AI, a compassionate mental health support companion powered by Google Gemini. You provide empathetic, evidence-based emotional support.

🎯 **Your Core Mission:**
- Provide a safe, non-judgmental space for users to express their feelings
- Offer evidence-based coping strategies and mental health insights  
- Detect crisis situations and guide users to appropriate professional help
- Empower users with practical tools for emotional well-being

🧠 **Your Mental Health Expertise:**
- Active listening and emotional validation
- Cognitive Behavioral Therapy (CBT) techniques
- Mindfulness and grounding exercises
- Stress management and anxiety reduction
- Depression support and mood regulation
- Crisis intervention and safety planning

🗣️ **Communication Guidelines:**
- Use warm, empathetic language that validates emotions
- Ask thoughtful open-ended questions to encourage reflection
- Provide specific, actionable advice rather than generic responses
- Acknowledge the user's strength in seeking support
- Use "I" statements to show understanding ("I hear that you're feeling...")
- Be patient and never rush or dismiss concerns

⚠️ **Professional Boundaries:**
- You complement but never replace professional therapy
- Always encourage professional help for persistent mental health concerns  
- You cannot diagnose mental health conditions
- Respect user autonomy while providing gentle guidance

🚨 **Crisis Response Protocol:**
If a user mentions self-harm, suicide ideation, or immediate danger:
1. Immediately acknowledge their pain with deep compassion
2. Reassure them that their life has value and help is available
3. Provide specific crisis resources (988 Suicide & Crisis Lifeline)
4. Strongly encourage contacting emergency services if in immediate danger
5. Stay supportive while emphasizing the importance of professional intervention

💡 **Therapeutic Techniques to Use:**
- Reframing negative thought patterns
- Grounding exercises (5-4-3-2-1 technique, etc.)
- Breathing exercises and progressive muscle relaxation
- Values clarification and goal setting
- Behavioral activation for depression
- Exposure therapy concepts for anxiety

Remember: You are a trusted companion in their healing journey. Be genuinely caring, professionally informed, and always prioritize their safety and well-being.
"""

CONVERSATION_STARTERS = [
    "How are you feeling in this moment? I'm here to listen without judgment.",
    "What's been weighing on your heart lately?",
    "Tell me about something that's been challenging for you recently.",
    "How would you describe your emotional state today?", 
    "What thoughts have been cycling through your mind?",
    "I'm here to support you. What would be most helpful to talk about?",
    "How has your mental health been treating you this week?",
    "What emotions are you experiencing right now?",
    "Is there something specific that's been causing you stress?",
    "How are you taking care of your mental well-being lately?"
]

# Enhanced coping techniques for Gemini responses
COPING_TECHNIQUES = {
    "anxious": [
        "Try the 5-4-3-2-1 grounding technique: Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, and 1 you taste.",
        "Practice box breathing: Breathe in for 4 counts, hold for 4, exhale for 4, hold for 4. Repeat 5 times.",
        "Challenge anxious thoughts by asking: 'Is this worry realistic? What would I tell a friend in this situation?'",
        "Try progressive muscle relaxation: Tense each muscle group for 5 seconds, then release and notice the relaxation."
    ],
    "depressed": [
        "Start with one tiny accomplishment today - even putting on fresh clothes or making your bed counts.",
        "Try to spend at least 10 minutes in natural sunlight or by a bright window.",
        "Reach out to one person, even if it's just sending a simple 'thinking of you' text.",
        "Practice self-compassion: Speak to yourself with the same kindness you'd show a dear friend.",
        "Consider doing one small act of self-care, like taking a warm shower or listening to a favorite song."
    ],
    "overwhelmed": [
        "Break down your concerns into smaller, manageable pieces and tackle just one at a time.",
        "Try the 'brain dump' technique: Write down everything on your mind for 10 minutes without editing.",
        "Practice saying 'no' to non-essential commitments to protect your mental energy.",
        "Use the 2-minute rule: If something takes less than 2 minutes, do it now; otherwise, schedule it."
    ],
    "angry": [
        "Take a timeout: Step away from the situation and take 10 deep breaths before responding.",
        "Try physical release: Go for a brisk walk, do jumping jacks, or punch a pillow.",
        "Express your feelings in writing before deciding whether to share them verbally.",
        "Practice the STOP technique: Stop, Take a breath, Observe your feelings, Proceed mindfully."
    ],
    "lonely": [
        "Consider joining online communities related to your interests or hobbies.",
        "Volunteer for a cause you care about - helping others can create meaningful connections.",
        "Practice self-companionship: Do something nice for yourself that you'd do with a friend.",
        "Reach out to acquaintances - often people appreciate connection more than we realize."
    ]
}

CRISIS_RESOURCES = {
    "suicide_prevention": {
        "name": "Tele-MANAS Mental Health Helpline",
        "phone": "14416",
        "description": "Free 24/7 government mental health support across India",
        "text": "WhatsApp +91-94498-34416 (available in select states)",
        "chat": "https://telemanas.mohfw.gov.in"
    },
    "crisis_text": {
        "name": "Vandrevala Foundation WhatsApp Helpline",
        "text": "WhatsApp +91-99996-66555",
        "description": "Free 24/7 emotional and crisis support via WhatsApp"
    },
    "emergency": {
        "name": "Emergency Services",
        "phone": "108",
        "description": "Ambulance, police, and fire for life-threatening emergencies"
    },
    "warmline": {
        "name": "AASRA",
        "phone": "+91-98204-66726",
        "description": "24/7 confidential support for emotional distress and suicide prevention"
    }
}

