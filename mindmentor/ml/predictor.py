# ml/predictor.py
import joblib
import numpy as np
import os
import json
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "mindmentor_model.joblib")
MLB_PATH = os.path.join(os.path.dirname(__file__), "mindmentor_mlb.joblib")
META_PATH = os.path.join(os.path.dirname(__file__), "model_metadata.json")

model = joblib.load(MODEL_PATH)
mlb = joblib.load(MLB_PATH)

with open(META_PATH, "r") as f:
    metadata = json.load(f)

FEATURES = metadata["features"]
TAG_NAMES = metadata["tag_names"]

# Use thresholds from metadata if available, otherwise use optimized ones
OPTIMIZED_THRESHOLDS = metadata.get("thresholds", {
    "Addiction": 0.25,
    "Anxiety Disorder": 0.35,
    "Apathy": 0.4,
    "Burnout": 0.4,
    "Depression": 0.3,
    "Disordered Eating": 0.3,
    "Generalized Anxiety": 0.35,
    "Healthy": 0.7,
    "Hopelessness": 0.4,
    "Hypersomnia": 0.5,
    "Insomnia": 0.4,
    "Isolation Risk": 0.4,
    "Low Self-Esteem": 0.4,
    "Low Self-Worth": 0.3,
    "Mood Swings": 0.5,
    "Substance Dependence": 0.2
})

def predict_mood(input_data: dict, use_thresholds=True):
    try:
        # Remove features that were excluded during training
        cleaned_data = input_data.copy()
        if "gender" in cleaned_data:
            del cleaned_data["gender"]
        if "substance_abuse" in cleaned_data:
            del cleaned_data["substance_abuse"]

        feature_values = []
        for feature in FEATURES:
            if feature in cleaned_data:
                feature_values.append(float(cleaned_data[feature]))
            else:
                print(f"Warning: Missing feature {feature}, using default value 0")
                feature_values.append(0.0)

        # Create DataFrame with proper feature names for sklearn
        X_df = pd.DataFrame([feature_values], columns=FEATURES)

        if use_thresholds:
            y_proba = model.predict_proba(X_df)
            
            if hasattr(y_proba, '__len__') and len(y_proba) > 0:
                if isinstance(y_proba[0], np.ndarray):
                    proba_values = np.array([prob[:, 1] if prob.shape[1] > 1 else prob[:, 0] for prob in y_proba]).T
                else:
                    proba_values = y_proba
            else:
                proba_values = y_proba

            y_pred = np.zeros((1, len(TAG_NAMES)))
            probabilities = {}
            
            for i, tag in enumerate(TAG_NAMES):
                threshold = OPTIMIZED_THRESHOLDS.get(tag, 0.5)
                if i < proba_values.shape[1]:
                    prob_score = float(proba_values[0, i])
                    probabilities[tag] = prob_score
                    y_pred[0, i] = int(prob_score >= threshold)
        else:
            y_pred = model.predict(X_df)
            probabilities = {}

        tags = []
        if y_pred[0].any():
            # Skip MLBinarizer entirely and use direct indexing
            predicted_indices = np.where(y_pred[0] == 1)[0]
            tags = [TAG_NAMES[i] for i in predicted_indices]
            print(f"Final extracted tags: {tags}")  # Debug

        confidence_score = calculate_confidence(tags, probabilities)
        direct_actions = generate_direct_actions(tags, input_data)

        return {
            "tags": tags,
            "probabilities": probabilities,
            "confidence": confidence_score,
            "direct_actions": direct_actions
        }

    except Exception as e:
        print(f"Prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return safe default structure
        return {
            "tags": [],
            "confidence": "low",
            "direct_actions": {
                "immediate_steps": [],
                "daily_habits": [],
                "weekly_goals": [],
                "lifestyle_changes": []
            },
            "probabilities": {}
        }

def calculate_confidence(tags, probabilities):
    if not tags or not probabilities:
        return "low"
    
    avg_probability = sum(probabilities.get(tag, 0) for tag in tags) / len(tags)
    
    if avg_probability > 0.8:
        return "high"
    elif avg_probability > 0.6:
        return "moderate"
    else:
        return "low"

def generate_direct_actions(tags, input_data):
    actions = {
        "immediate_steps": [],
        "daily_habits": [],
        "weekly_goals": [],
        "lifestyle_changes": []
    }
    
    priority_conditions = []
    secondary_conditions = []
    
    for tag in tags:
        if tag in ["Substance Dependence", "Addiction", "Depression"]:
            priority_conditions.append(tag)
        else:
            secondary_conditions.append(tag)
    
    for tag in priority_conditions:
        tag_actions = get_direct_actions_for_tag(tag, input_data)
        merge_actions(actions, tag_actions)
    
    for tag in secondary_conditions:
        tag_actions = get_direct_actions_for_tag(tag, input_data)
        merge_actions(actions, tag_actions)
    
    if "Disordered Eating" in tags and "Low Self-Esteem" in tags:
        actions["immediate_steps"].append("Focus on nourishing your body as an act of self-care")
    
    if "Addiction" in tags and any(tag in tags for tag in ["Depression", "Anxiety Disorder"]):
        actions["immediate_steps"].append("Avoid using substances to cope with emotional distress")
    
    for key in actions:
        actions[key] = list(set(actions[key]))
    
    return actions

def merge_actions(main_actions, new_actions):
    for key in main_actions:
        if key in new_actions:
            main_actions[key].extend(new_actions[key])

def get_direct_actions_for_tag(tag, input_data):
    if tag == "Anxiety Disorder" or tag == "Generalized Anxiety":
        return get_anxiety_actions(input_data)
    elif tag == "Depression":
        return get_depression_actions(input_data)
    elif tag == "Low Self-Esteem" or tag == "Low Self-Worth":
        return get_self_esteem_actions(input_data)
    elif tag == "Insomnia":
        return get_sleep_actions(input_data)
    elif tag == "Burnout":
        return get_burnout_actions(input_data)
    elif tag == "Isolation Risk":
        return get_social_actions(input_data)
    elif tag == "Disordered Eating":
        return get_eating_actions(input_data)
    elif tag == "Mood Swings":
        return get_mood_regulation_actions(input_data)
    elif tag == "Apathy":
        return get_motivation_actions(input_data)
    elif tag == "Hypersomnia":
        return get_oversleep_actions(input_data)
    elif tag == "Addiction" or tag == "Substance Dependence":
        return get_addiction_actions(input_data)
    else:
        return get_general_wellness_actions(input_data)

def get_anxiety_actions(input_data):
    actions = {
        "immediate_steps": [
            "Practice 4-7-8 breathing: inhale for 4, hold for 7, exhale for 8",
            "Use the 5-4-3-2-1 grounding technique when feeling overwhelmed"
        ],
        "daily_habits": [
            "Limit caffeine intake to before 2 PM",
            "Spend 10 minutes outdoors in natural light each morning"
        ],
        "weekly_goals": [],
        "lifestyle_changes": []
    }
    
    if input_data.get("sociability", 5) < 4:
        actions["weekly_goals"].append("Attend one social event or gathering per week")
        actions["daily_habits"].append("Make small talk with one person daily")
    
    if input_data.get("stress_level", 5) > 7:
        actions["daily_habits"].append("Do 15 minutes of physical activity to release tension")
        actions["lifestyle_changes"].append("Identify and eliminate one major stressor from your routine")
    
    if input_data.get("sleep_hours", 7) < 6:
        actions["immediate_steps"].append("Set a consistent bedtime starting tonight")
    
    actions["weekly_goals"].extend([
        "Try one new relaxation technique",
        "Go for a 20-minute walk in a park or quiet area"
    ])
    
    return actions

def get_depression_actions(input_data):
    actions = {
        "immediate_steps": [
            "Get sunlight exposure for 15 minutes today",
            "Complete one small task you've been putting off"
        ],
        "daily_habits": [
            "Make your bed every morning",
            "Write down one thing you accomplished, no matter how small"
        ],
        "weekly_goals": [
            "Schedule one enjoyable activity for this week",
            "Reach out to one friend or family member"
        ],
        "lifestyle_changes": []
    }
    
    if input_data.get("motivation", 5) < 4:
        actions["immediate_steps"].append("Break your biggest task into 3 smaller steps")
        actions["daily_habits"].append("Set one achievable goal each morning")
    
    if input_data.get("sociability", 5) < 4:
        actions["weekly_goals"].append("Join one group activity or club")
        actions["daily_habits"].append("Send one text message to maintain social connections")
    
    if input_data.get("sleep_hours", 7) > 9:
        actions["daily_habits"].append("Set an alarm and get up at the same time every day")
    
    actions["lifestyle_changes"].extend([
        "Establish a morning routine that includes physical movement",
        "Create a weekly schedule with structured activities"
    ])
    
    return actions

def get_self_esteem_actions(input_data):
    actions = {
        "immediate_steps": [
            "Write down 3 things you did well today",
            "Replace one negative self-thought with a neutral or positive one"
        ],
        "daily_habits": [
            "Practice positive self-talk in the mirror for 2 minutes",
            "Celebrate small wins by acknowledging them out loud"
        ],
        "weekly_goals": [
            "Learn one new skill or hobby",
            "Do something you're genuinely good at"
        ],
        "lifestyle_changes": [
            "Surround yourself with supportive people who appreciate you",
            "Set boundaries with people who consistently bring you down"
        ]
    }
    
    if input_data.get("motivation", 5) < 4:
        actions["daily_habits"].append("Set and complete one small personal goal daily")
    
    if input_data.get("sociability", 5) < 4:
        actions["weekly_goals"].append("Give someone a genuine compliment")
    
    return actions

def get_sleep_actions(input_data):
    sleep_hours = input_data.get("sleep_hours", 7)
    
    actions = {
        "immediate_steps": [
            "Put away all screens 1 hour before your target bedtime tonight",
            "Set your bedroom temperature to 65-68°F"
        ],
        "daily_habits": [
            "Go to bed and wake up at the same time every day",
            "Avoid large meals and caffeine 3 hours before bedtime"
        ],
        "weekly_goals": [
            "Create a relaxing bedtime routine",
            "Evaluate your mattress and pillows for comfort"
        ],
        "lifestyle_changes": [
            "Make your bedroom a sleep-only zone",
            "Get morning sunlight exposure to regulate your circadian rhythm"
        ]
    }
    
    if sleep_hours < 6:
        actions["immediate_steps"].append("Move your bedtime 15 minutes earlier starting tonight")
    elif sleep_hours > 9:
        actions["immediate_steps"].append("Set an alarm and force yourself to get up at a consistent time")
    
    if input_data.get("stress_level", 5) > 7:
        actions["daily_habits"].append("Do 10 minutes of relaxation exercises before bed")
    
    return actions

def get_burnout_actions(input_data):
    actions = {
        "immediate_steps": [
            "Take a 15-minute break from whatever you're doing right now",
            "Say 'no' to one non-essential commitment this week"
        ],
        "daily_habits": [
            "Take a 5-minute break every hour during work/study",
            "Do one thing purely for enjoyment each day"
        ],
        "weekly_goals": [
            "Schedule one full day with no work or academic responsibilities",
            "Delegate or eliminate one recurring task"
        ],
        "lifestyle_changes": [
            "Set clear boundaries between work/study time and personal time",
            "Learn to prioritize tasks and let go of perfectionism"
        ]
    }
    
    if input_data.get("stress_level", 5) > 7:
        actions["daily_habits"].append("Practice time-blocking to manage your schedule better")
    
    if input_data.get("motivation", 5) < 4:
        actions["immediate_steps"].append("Focus on completing just one important task today")
    
    return actions

def get_social_actions(input_data):
    actions = {
        "immediate_steps": [
            "Send a text to someone you haven't talked to in a while",
            "Smile and make eye contact with people you encounter today"
        ],
        "daily_habits": [
            "Have one meaningful conversation with someone each day",
            "Leave your room/house for at least 30 minutes daily"
        ],
        "weekly_goals": [
            "Attend one social event, club meeting, or group activity",
            "Invite someone to do an activity together"
        ],
        "lifestyle_changes": [
            "Join a club, sports team, or volunteer organization",
            "Create regular social commitments"
        ]
    }
    
    if input_data.get("anxiety", 5) > 6:
        actions["immediate_steps"].append("Start with low-pressure social interactions")
    
    return actions

def get_eating_actions(input_data):
    eating_score = input_data.get("eating_habits", 5)
    
    actions = {
        "immediate_steps": [
            "Plan and eat three balanced meals today",
            "Drink a glass of water before each meal"
        ],
        "daily_habits": [
            "Eat meals at consistent times without distractions",
            "Include protein, healthy fats, and vegetables in each meal"
        ],
        "weekly_goals": [
            "Meal prep for 3-4 days in advance",
            "Try one new healthy recipe"
        ],
        "lifestyle_changes": [
            "Keep healthy snacks readily available",
            "Create a supportive eating environment at home"
        ]
    }
    
    if eating_score < 4:
        actions["immediate_steps"].append("Set reminders to eat regular meals")
        actions["daily_habits"].append("Keep a food diary to track eating patterns")
    elif eating_score > 7:
        actions["daily_habits"].append("Practice mindful eating - eat slowly and pay attention to hunger cues")
    
    return actions

def get_mood_regulation_actions(input_data):
    actions = {
        "immediate_steps": [
            "Take 10 deep breaths when you feel your mood shifting",
            "Remove yourself from triggering situations for 5 minutes"
        ],
        "daily_habits": [
            "Track your mood and identify triggers in a journal",
            "Practice one grounding technique when emotions feel intense"
        ],
        "weekly_goals": [
            "Identify your top 3 mood triggers and plan responses",
            "Learn one new emotion regulation technique"
        ],
        "lifestyle_changes": [
            "Establish consistent daily routines to provide stability",
            "Avoid alcohol and substances that can worsen mood swings"
        ]
    }
    
    if input_data.get("stress_level", 5) > 7:
        actions["daily_habits"].append("Do 15 minutes of physical exercise to regulate emotions")
    
    return actions

def get_motivation_actions(input_data):
    actions = {
        "immediate_steps": [
            "Choose one small task and complete it within the next hour",
            "Change your environment - go to a different room or location"
        ],
        "daily_habits": [
            "Start each day by completing one easy task to build momentum",
            "Set a timer for 25 minutes and work on something important"
        ],
        "weekly_goals": [
            "Set one meaningful goal and break it into daily steps",
            "Find an accountability partner for your goals"
        ],
        "lifestyle_changes": [
            "Identify what activities naturally energize you and do more of them",
            "Remove or minimize activities that drain your energy unnecessarily"
        ]
    }
    
    if input_data.get("sociability", 5) < 4:
        actions["weekly_goals"].append("Join a group or community related to your interests")
    
    return actions

def get_oversleep_actions(input_data):
    actions = {
        "immediate_steps": [
            "Set multiple alarms 5 minutes apart starting tomorrow",
            "Place your alarm clock across the room so you have to get up"
        ],
        "daily_habits": [
            "Get bright light exposure immediately upon waking",
            "Have a consistent morning routine that requires you to stay awake"
        ],
        "weekly_goals": [
            "Gradually reduce sleep time by 15 minutes each day until you reach 7-8 hours",
            "Schedule morning activities that you enjoy"
        ],
        "lifestyle_changes": [
            "Avoid daytime naps longer than 20 minutes",
            "Create an engaging reason to get up each morning"
        ]
    }
    
    return actions

def get_addiction_actions(input_data):
    actions = {
        "immediate_steps": [
            "Remove or secure access to substances for the next 24 hours",
            "Identify your main triggers for substance use today"
        ],
        "daily_habits": [
            "Replace substance use times with healthy activities",
            "Check in with yourself hourly about cravings and feelings"
        ],
        "weekly_goals": [
            "Find one new healthy coping mechanism to try",
            "Connect with someone who supports your recovery"
        ],
        "lifestyle_changes": [
            "Avoid environments and people associated with substance use",
            "Build a routine that doesn't revolve around substances"
        ]
    }
    
    if input_data.get("stress_level", 5) > 7:
        actions["daily_habits"].append("Practice stress management techniques instead of using substances")
    
    if input_data.get("sociability", 5) < 4:
        actions["weekly_goals"].append("Find sober social activities and communities")
    
    return actions

def get_general_wellness_actions(input_data):
    actions = {
        "immediate_steps": [
            "Take 5 deep breaths and check in with how you're feeling",
            "Drink a glass of water and do some light stretching"
        ],
        "daily_habits": [
            "Spend 10 minutes in nature or by a window with natural light",
            "Do one thing that brings you joy each day"
        ],
        "weekly_goals": [
            "Try one new activity that interests you",
            "Connect with someone who makes you feel good about yourself"
        ],
        "lifestyle_changes": [
            "Maintain consistent sleep and meal schedules",
            "Build a support network of people who care about your wellbeing"
        ]
    }
    
    return actions

def debug_prediction(input_data):
    print("=== DEBUGGING PREDICTION ===")
    print(f"Input data: {input_data}")
    
    result = predict_mood(input_data)
    
    print(f"Final tags: {result['tags']}")
    print(f"Confidence: {result['confidence']}")
    
    print("Threshold Analysis:")
    for tag, prob in result['probabilities'].items():
        threshold = OPTIMIZED_THRESHOLDS.get(tag, 0.5)
        if prob > 0.1:
            print(f"  {tag}: {prob:.3f} (threshold: {threshold:.3f}) {'✓' if prob >= threshold else '✗'}")
    
    return result