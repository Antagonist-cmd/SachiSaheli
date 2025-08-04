# ml/predictor.py
import joblib
import numpy as np
import os
import json
import pandas as pd
from .ai_suggestions import generate_ai_suggestions

MODEL_PATH = os.path.join(os.path.dirname(__file__), "mindmentor_model.joblib")
MLB_PATH = os.path.join(os.path.dirname(__file__), "mindmentor_mlb.joblib")
META_PATH = os.path.join(os.path.dirname(__file__), "model_metadata.json")

model = joblib.load(MODEL_PATH)
mlb = joblib.load(MLB_PATH)

with open(META_PATH, "r") as f:
    metadata = json.load(f)

# Keep ALL features including substance_abuse
FEATURES = metadata["features"]
TAG_NAMES = metadata["tag_names"]

# Use ALL thresholds including substance-related ones
OPTIMIZED_THRESHOLDS = metadata.get("thresholds", {})

def calculate_composite_indicators(input_data):
    """Calculate weighted mental health indicators for complex conditions"""
    
    # Anxiety composite (stress + anxiety)
    anxiety_score = (
        input_data.get("stress_level", 5) * 0.4 +
        input_data.get("anxiety", 5) * 0.6
    ) / 10.0
    
    # Depression composite (multiple factors)
    depression_score = (
        (10 - input_data.get("motivation", 5)) * 0.25 +  # Reduced motivation impact
        (10 - input_data.get("emotional_stability", 5)) * 0.35 +
        (10 - input_data.get("self_esteem", 5)) * 0.4
    ) / 10.0
    
    # Burnout (stress + low motivation)
    burnout_score = (
        input_data.get("stress_level", 5) * 0.6 +
        (10 - input_data.get("motivation", 5)) * 0.4
    ) / 10.0
    
    # Sleep indicators
    sleep_hours = input_data.get("sleep_hours", 7)
    insomnia_score = max(0, (7 - sleep_hours) / 7.0) if sleep_hours < 7 else 0
    hypersomnia_score = max(0, (sleep_hours - 8) / 4.0) if sleep_hours > 8 else 0
    
    # Social isolation
    isolation_score = (10 - input_data.get("sociability", 5)) / 10.0
    
    # Self-esteem issues
    self_esteem_score = (10 - input_data.get("self_esteem", 5)) / 10.0
    
    # Eating disorder risk
    eating_habits = input_data.get("eating_habits", 5)
    eating_score = abs(eating_habits - 5) / 5.0
    
    # Apathy (primarily low motivation, but not overpowering)
    apathy_score = (10 - input_data.get("motivation", 5)) / 10.0
    
    # Substance abuse composite scoring
    substance_score = float(input_data.get("substance_abuse", 0))
    
    return {
        "anxiety": anxiety_score,
        "depression": depression_score,
        "burnout": burnout_score,
        "insomnia": insomnia_score,
        "hypersomnia": hypersomnia_score,
        "isolation": isolation_score,
        "self_esteem": self_esteem_score,
        "eating": eating_score,
        "apathy": apathy_score,
        "substance": substance_score
    }

def predict_mood(input_data: dict, use_thresholds=True):
    try:
        # Keep all input data including substance_abuse
        cleaned_data = input_data.copy()
        
        # Build feature vector with ALL features including substance_abuse
        feature_values = []
        for feature in FEATURES:
            if feature in cleaned_data:
                if feature == "gender":
                    # Map gender to numeric
                    gender_map = {"male": 0, "female": 1, "other": 2, "prefer-not-to-say": 2}
                    feature_values.append(float(gender_map.get(cleaned_data[feature], 0)))
                else:
                    feature_values.append(float(cleaned_data[feature]))
            else:
                # Defaults for all features
                defaults = {
                    "age": 20, "gender": 0, "stress_level": 5, "sleep_hours": 7,
                    "sociability": 5, "anxiety": 5, "emotional_stability": 5,
                    "self_esteem": 5, "motivation": 5, "eating_habits": 5,
                    "substance_abuse": 0
                }
                feature_values.append(float(defaults.get(feature, 5)))

        # Create DataFrame with correct feature order
        X_df = pd.DataFrame([feature_values], columns=FEATURES)

        # Get ML model probabilities
        y_proba = model.predict_proba(X_df)
        
        if hasattr(y_proba, '__len__') and len(y_proba) > 0:
            if isinstance(y_proba[0], np.ndarray):
                proba_values = np.array([prob[:, 1] if prob.shape[1] > 1 else prob[:, 0] for prob in y_proba]).T
            else:
                proba_values = y_proba
        else:
            proba_values = y_proba

        # Calculate composite scores
        composite_scores = calculate_composite_indicators(input_data)
        
        probabilities = {}
        y_pred = np.zeros((1, len(TAG_NAMES)))
        
        # Enhanced prediction with composite scoring
        for i, tag in enumerate(TAG_NAMES):
            # Process ALL tags including substance-related ones
            
            # Get base probability from ML model
            if i < proba_values.shape[1]:
                base_prob = float(proba_values[0, i])
            else:
                base_prob = 0.0
            
            # Apply composite scoring boosts
            final_prob = base_prob
            
            if tag == "Anxiety Disorder":
                final_prob += composite_scores["anxiety"] * 0.3
                
            elif tag == "Generalized Anxiety":
                final_prob += composite_scores["anxiety"] * 0.25
                
            elif tag == "Depression":
                final_prob += composite_scores["depression"] * 0.4
                
            elif tag == "Burnout":
                final_prob += composite_scores["burnout"] * 0.35
                
            elif tag == "Apathy":
                final_prob += composite_scores["apathy"] * 0.3
                # Special case for very low motivation
                if input_data.get("motivation", 5) <= 2:
                    final_prob += 0.25
                    
            elif tag == "Isolation Risk":
                final_prob += composite_scores["isolation"] * 0.4
                # Special case for very low sociability
                if input_data.get("sociability", 5) <= 1:
                    final_prob += 0.3
                    
            elif tag == "Insomnia":
                final_prob += composite_scores["insomnia"] * 0.4
                
            elif tag == "Hypersomnia":
                final_prob += composite_scores["hypersomnia"] * 0.4
                
            elif tag in ["Low Self-Esteem", "Low Self-Worth"]:
                final_prob += composite_scores["self_esteem"] * 0.3
                
            elif tag == "Disordered Eating":
                final_prob += composite_scores["eating"] * 0.25
                
            elif tag == "Mood Swings":
                # Mood swings from emotional instability
                if input_data.get("emotional_stability", 5) <= 3:
                    final_prob += 0.3
                    
            elif tag == "Hopelessness":
                # Combination of low mood factors
                hopelessness_composite = (composite_scores["depression"] + composite_scores["apathy"]) / 2
                final_prob += hopelessness_composite * 0.3
                
            # Substance-related tag processing
            elif tag in ["Addiction", "Substance Dependence"]:
                # Boost probability if substance_abuse = 1
                final_prob += composite_scores["substance"] * 0.5
                # Additional boost for multiple risk factors
                if (composite_scores["depression"] > 0.6 or 
                    composite_scores["anxiety"] > 0.6 or 
                    composite_scores["isolation"] > 0.6):
                    final_prob += 0.2

            # Cap at 1.0
            final_prob = min(final_prob, 1.0)
            probabilities[tag] = final_prob
            
            # Apply threshold
            threshold = OPTIMIZED_THRESHOLDS.get(tag, 0.4)
            if final_prob >= threshold:
                y_pred[0, i] = 1

        # Extract ALL predicted tags (including substance tags)
        tags = []
        if y_pred[0].any():
            predicted_indices = np.where(y_pred[0] == 1)[0]
            tags = [TAG_NAMES[i] for i in predicted_indices]

        # Fallback logic - ensure something is always returned
        if not tags:
            # Check if person seems generally healthy
            overall_score = (
                input_data.get("stress_level", 5) +
                input_data.get("anxiety", 5) +
                (10 - input_data.get("emotional_stability", 5)) +
                (10 - input_data.get("self_esteem", 5))
            ) / 4
            
            if overall_score <= 4:  # Generally good indicators
                tags.append("Healthy")
            else:
                # Find the most likely condition based on composite scores
                max_score = max(composite_scores.values())
                if max_score > 0.5:
                    if composite_scores["anxiety"] == max_score:
                        tags.append("Generalized Anxiety")
                    elif composite_scores["depression"] == max_score:
                        tags.append("Depression")
                    elif composite_scores["isolation"] == max_score:
                        tags.append("Isolation Risk")
                    elif composite_scores["apathy"] == max_score:
                        tags.append("Apathy")
                else:
                    tags.append("Healthy")

        print(f"Final extracted tags: {tags}")
        
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
        
        return {
            "tags": ["Monitoring Needed"],
            "confidence": "low",
            "direct_actions": {
                "immediate_steps": ["Take a moment to reflect on your current state"],
                "daily_habits": ["Check in with yourself regularly"],
                "weekly_goals": ["Consider talking to someone you trust"],
                "lifestyle_changes": []
            },
            "probabilities": {}
        }

def calculate_confidence(tags, probabilities):
    if not tags or not probabilities:
        return "low"
    
    avg_probability = sum(probabilities.get(tag, 0) for tag in tags) / len(tags)
    
    if avg_probability > 0.7:
        return "high"
    elif avg_probability > 0.5:
        return "moderate"
    else:
        return "low"

def generate_direct_actions(tags, input_data):
    """Generate AI-powered personalized suggestions"""
    journal_entry = input_data.get("journal_entry", "")
    
    # Use AI to generate dynamic suggestions
    ai_suggestions = generate_ai_suggestions(tags, input_data, journal_entry)
    
    return ai_suggestions

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
