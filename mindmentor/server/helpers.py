import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from utils.supabase_client import supabase
from datetime import datetime, timedelta
from collections import Counter
import json
import csv
from io import StringIO
from flask import Response

def get_user_profile_data(user_id):
    """Fetch user profile from profiles table"""
    try:
        response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        return response.data if response.data else {}
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return {}

def get_user_mood_stats(user_id):
    """Calculate mood statistics from mood_checkins"""
    try:
        response = supabase.table("mood_checkins").select("*").eq("user_id", user_id).order("timestamp", desc=True).execute()
        checkins = response.data if response.data else []
        
        # Calculate streak
        streak = calculate_user_streak(checkins)
        
        # Total check-ins
        num_checkins = len(checkins)
        
        # Top mood from diagnosis_tags
        all_tags = []
        for checkin in checkins:
            if checkin.get("diagnosis_tags"):
                all_tags.extend(checkin["diagnosis_tags"])
        
        top_mood = Counter(all_tags).most_common(1)[0][0] if all_tags else "No data yet"
        
        return {
            "streak": streak,
            "num_checkins": num_checkins, 
            "top_mood": top_mood
        }
    except Exception as e:
        print(f"Error fetching mood stats: {e}")
        return {"streak": 0, "num_checkins": 0, "top_mood": "No data yet"}

def calculate_user_streak(checkins):
    """Calculate consecutive daily check-in streak"""
    if not checkins:
        return 0
    
    # Get unique dates from checkins
    checkin_dates = []
    for checkin in checkins:
        date_str = checkin["timestamp"][:10]  # Get YYYY-MM-DD part
        if date_str not in checkin_dates:
            checkin_dates.append(date_str)
    
    checkin_dates.sort(reverse=True)  # Most recent first
    
    today = datetime.now().date()
    streak = 0
    
    for i, date_str in enumerate(checkin_dates):
        checkin_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        expected_date = today - timedelta(days=i)
        
        if checkin_date == expected_date or (i == 0 and (today - checkin_date).days == 1):
            streak += 1
        else:
            break
    
    return streak

def get_user_badges(user_id):
    """Generate achievement badges based on user activity"""
    try:
        # Get mood stats
        mood_stats = get_user_mood_stats(user_id)
        badges = []
        
        # Streak badges
        if mood_stats["streak"] >= 7:
            badges.append("🔥 7-Day Streak")
        if mood_stats["streak"] >= 30:
            badges.append("🔥 Monthly Champion")
        
        # Check-in badges
        if mood_stats["num_checkins"] >= 5:
            badges.append("📊 Getting Started")
        if mood_stats["num_checkins"] >= 25:
            badges.append("📊 Check-in Pro")
        if mood_stats["num_checkins"] >= 50:
            badges.append("📊 Wellness Warrior")
        
        # Journal badges
        journal_count = get_journal_count(user_id)
        if journal_count >= 3:
            badges.append("📝 Journaling Beginner")
        if journal_count >= 10:
            badges.append("📝 Reflection Master")
        
        return badges
    except Exception as e:
        print(f"Error generating badges: {e}")
        return []

def get_recent_journals(user_id, limit=3):
    """Fetch recent journal entries"""
    try:
        response = supabase.table("journals").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching journals: {e}")
        return []

def get_journal_count(user_id):
    """Get total journal count"""
    try:
        response = supabase.table("journals").select("id", count="exact").eq("user_id", user_id).execute()
        return response.count if response.count else 0
    except Exception as e:
        return 0

def get_top_gratitude(user_id, limit=3):
    """Fetch recent gratitude entries"""
    try:
        response = supabase.table("gratitude_entries").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching gratitude: {e}")
        return []

def export_user_data(user_id, format='json'):
    """Export all user data in JSON or CSV format"""
    try:
        # Get all user data
        profile_data = get_user_profile_data(user_id)
        
        # Get all mood check-ins
        mood_response = supabase.table("mood_checkins").select("*").eq("user_id", user_id).order("timestamp", desc=True).execute()
        mood_data = mood_response.data if mood_response.data else []
        
        # Get all journals  
        journal_response = supabase.table("journals").select("*").eq("user_id", user_id).order("timestamp", desc=True).execute()
        journal_data = journal_response.data if journal_response.data else []
        
        # Get all gratitude entries
        gratitude_response = supabase.table("gratitude_entries").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        gratitude_data = gratitude_response.data if gratitude_response.data else []
        
        # Combine all data
        export_data = {
            "profile": profile_data,
            "mood_checkins": mood_data,
            "journals": journal_data,
            "gratitude_entries": gratitude_data,
            "export_date": datetime.now().isoformat(),
            "total_records": {
                "mood_checkins": len(mood_data),
                "journals": len(journal_data),
                "gratitude_entries": len(gratitude_data)
            }
        }
        
        if format == 'csv':
            return export_to_csv(export_data)
        else:
            return export_data
            
    except Exception as e:
        print(f"Error exporting data: {e}")
        return None

def export_to_csv(data):
    """Convert export data to CSV format"""
    output = StringIO()
    
    # Write mood check-ins
    if data['mood_checkins']:
        writer = csv.DictWriter(output, fieldnames=data['mood_checkins'][0].keys() if data['mood_checkins'] else [])
        output.write("=== MOOD CHECK-INS ===\n")
        writer.writeheader()
        writer.writerows(data['mood_checkins'])
        output.write("\n")
    
    # Write journals
    if data['journals']:
        writer = csv.DictWriter(output, fieldnames=data['journals'][0].keys() if data['journals'] else [])
        output.write("=== JOURNAL ENTRIES ===\n")
        writer.writeheader()
        writer.writerows(data['journals'])
        output.write("\n")
    
    # Write gratitude entries
    if data['gratitude_entries']:
        writer = csv.DictWriter(output, fieldnames=data['gratitude_entries'][0].keys() if data['gratitude_entries'] else [])
        output.write("=== GRATITUDE ENTRIES ===\n")
        writer.writeheader()
        writer.writerows(data['gratitude_entries'])
    
    return output.getvalue()

def get_mood_analytics(user_id, days=30):
    """Get mood trends and analytics for the last N days"""
    try:
        from datetime import datetime, timedelta
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        response = supabase.table("mood_checkins").select(
            "timestamp, stress_level, anxiety, emotional_stability, self_esteem, motivation, diagnosis_tags"
        ).eq("user_id", user_id).gte("timestamp", start_date.isoformat()).execute()
        
        checkins = response.data if response.data else []
        
        if not checkins:
            return {"avg_metrics": {}, "mood_distribution": {}, "improvement_areas": []}
        
        # Calculate average metrics
        metrics = ['stress_level', 'anxiety', 'emotional_stability', 'self_esteem', 'motivation']
        avg_metrics = {}
        
        for metric in metrics:
            values = [float(c[metric]) for c in checkins if c.get(metric) is not None]
            avg_metrics[metric] = round(sum(values) / len(values), 1) if values else 0
        
        # Mood distribution from diagnosis_tags
        all_tags = []
        for checkin in checkins:
            if checkin.get("diagnosis_tags"):
                all_tags.extend(checkin["diagnosis_tags"])
        
        mood_distribution = dict(Counter(all_tags).most_common(5))
        
        # Improvement areas (metrics that improved over time)
        improvement_areas = calculate_improvements(checkins, metrics)
        
        return {
            "avg_metrics": avg_metrics,
            "mood_distribution": mood_distribution,
            "improvement_areas": improvement_areas,
            "total_checkins": len(checkins)
        }
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        return {"avg_metrics": {}, "mood_distribution": {}, "improvement_areas": []}

def calculate_improvements(checkins, metrics):
    """Calculate which metrics have improved over time"""
    if len(checkins) < 4:  # Need at least 4 data points
        return []
    
    improvements = []
    
    # Sort by timestamp
    sorted_checkins = sorted(checkins, key=lambda x: x['timestamp'])
    
    # Compare first half vs second half averages
    mid_point = len(sorted_checkins) // 2
    first_half = sorted_checkins[:mid_point]
    second_half = sorted_checkins[mid_point:]
    
    for metric in metrics:
        # Get averages for each half
        first_vals = [float(c[metric]) for c in first_half if c.get(metric) is not None]
        second_vals = [float(c[metric]) for c in second_half if c.get(metric) is not None]
        
        if first_vals and second_vals:
            first_avg = sum(first_vals) / len(first_vals)
            second_avg = sum(second_vals) / len(second_vals)
            
            # For positive metrics (emotional_stability, self_esteem, motivation)
            if metric in ['emotional_stability', 'self_esteem', 'motivation']:
                if second_avg > first_avg + 0.5:  # Improved by at least 0.5 points
                    improvements.append({
                        "metric": metric.replace('_', ' ').title(),
                        "change": f"+{round(second_avg - first_avg, 1)}"
                    })
            # For negative metrics (stress, anxiety)
            else:
                if first_avg > second_avg + 0.5:  # Decreased by at least 0.5 points
                    improvements.append({
                        "metric": metric.replace('_', ' ').title(),
                        "change": f"-{round(first_avg - second_avg, 1)}"
                    })
    
    return improvements

def get_weekly_activity(user_id):
    """Get check-in activity for the last 7 days"""
    try:
        from datetime import datetime, timedelta
        
        week_ago = datetime.now() - timedelta(days=7)
        
        response = supabase.table("mood_checkins").select(
            "timestamp"
        ).eq("user_id", user_id).gte("timestamp", week_ago.isoformat()).execute()
        
        checkins = response.data if response.data else []
        
        # Group by day
        daily_activity = {}
        for checkin in checkins:
            day = checkin["timestamp"][:10]  # YYYY-MM-DD
            daily_activity[day] = daily_activity.get(day, 0) + 1
        
        return daily_activity
    except Exception as e:
        print(f"Error fetching weekly activity: {e}")
        return {}
