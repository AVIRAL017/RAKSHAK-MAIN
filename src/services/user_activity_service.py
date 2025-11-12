"""
SafeRoute Navigator v2.0 - User Activity Tracking Service
Tracks user route calculations, safety scores, and achievements for real profile data.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class UserActivityService:
    """Service for tracking user activity and generating profile statistics."""
    
    def __init__(self, data_dir: str = "data/users"):
        """Initialize the user activity service."""
        self.data_dir = data_dir
        self.activities_file = os.path.join(data_dir, "activities.json")
        self.achievements_file = os.path.join(data_dir, "achievements.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing data
        self.activities = self._load_activities()
        self.user_achievements = self._load_achievements()
        
        logger.info("🎯 User Activity Service initialized")
    
    def _load_activities(self) -> Dict:
        """Load user activities from file."""
        try:
            if os.path.exists(self.activities_file):
                with open(self.activities_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading activities: {e}")
            return {}
    
    def _save_activities(self):
        """Save user activities to file."""
        try:
            with open(self.activities_file, 'w') as f:
                json.dump(self.activities, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving activities: {e}")
    
    def _load_achievements(self) -> Dict:
        """Load user achievements from file."""
        try:
            if os.path.exists(self.achievements_file):
                with open(self.achievements_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading achievements: {e}")
            return {}
    
    def _save_achievements(self):
        """Save user achievements to file."""
        try:
            with open(self.achievements_file, 'w') as f:
                json.dump(self.user_achievements, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving achievements: {e}")
    
    def track_route_calculation(self, user_id: str, route_data: Dict):
        """Track a route calculation activity."""
        try:
            if user_id not in self.activities:
                self.activities[user_id] = {
                    "routes": [],
                    "total_distance": 0,
                    "total_time_saved": 0,
                    "safety_scores": [],
                    "route_types": {},
                    "activity_days": set(),
                    "member_since": datetime.now().isoformat()
                }
            
            user_activity = self.activities[user_id]
            
            # Add route record
            route_record = {
                "timestamp": datetime.now().isoformat(),
                "from": route_data.get("start_location", {}).get("resolved", "Unknown"),
                "to": route_data.get("end_location", {}).get("resolved", "Unknown"),
                "distance_km": route_data.get("route", {}).get("distance_km", 0),
                "duration_minutes": route_data.get("route", {}).get("duration_minutes", 0),
                "safety_score": route_data.get("safety", {}).get("safety_rating", "N/A"),
                "route_type": route_data.get("route", {}).get("route_type", "balanced")
            }
            
            user_activity["routes"].append(route_record)
            
            # Update aggregated stats
            distance = route_record["distance_km"]
            if isinstance(distance, (int, float)) and distance > 0:
                user_activity["total_distance"] += distance
            
            # Track safety score if numeric
            safety_score = self._extract_safety_score(route_record["safety_score"])
            if safety_score is not None:
                user_activity["safety_scores"].append(safety_score)
            
            # Track route type usage
            route_type = route_record["route_type"]
            if route_type not in user_activity["route_types"]:
                user_activity["route_types"][route_type] = 0
            user_activity["route_types"][route_type] += 1
            
            # Track activity day
            today = datetime.now().date().isoformat()
            if isinstance(user_activity["activity_days"], set):
                user_activity["activity_days"].add(today)
                # Convert set to list for JSON serialization
                user_activity["activity_days"] = list(user_activity["activity_days"])
            elif isinstance(user_activity["activity_days"], list):
                if today not in user_activity["activity_days"]:
                    user_activity["activity_days"].append(today)
            
            self._save_activities()
            
            # Check and update achievements
            self._update_achievements(user_id)
            
            logger.info(f"Route calculation tracked for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking route calculation: {e}")
    
    def _extract_safety_score(self, safety_rating) -> Optional[float]:
        """Extract numeric safety score from rating."""
        if isinstance(safety_rating, (int, float)):
            return float(safety_rating)
        elif isinstance(safety_rating, str):
            # Convert text ratings to numbers
            rating_map = {
                "excellent": 9.5, "very good": 8.5, "good": 7.5,
                "fair": 6.5, "poor": 5.0, "very poor": 3.0
            }
            return rating_map.get(safety_rating.lower(), None)
        return None
    
    def _update_achievements(self, user_id: str):
        """Check and update user achievements."""
        if user_id not in self.user_achievements:
            self.user_achievements[user_id] = {}
        
        user_activity = self.activities[user_id]
        user_achievements = self.user_achievements[user_id]
        
        # Achievement definitions
        achievements = {
            "first_route": {
                "name": "First Route",
                "description": "Calculated your first route",
                "check": lambda: len(user_activity["routes"]) >= 1
            },
            "safety_first": {
                "name": "Safety First", 
                "description": "Maintained 8.0+ average safety score",
                "check": lambda: len(user_activity["safety_scores"]) > 0 and 
                                sum(user_activity["safety_scores"]) / len(user_activity["safety_scores"]) >= 8.0
            },
            "explorer": {
                "name": "Explorer",
                "description": "Calculated 10+ different routes", 
                "check": lambda: len(user_activity["routes"]) >= 10
            },
            "distance_king": {
                "name": "Distance King",
                "description": "Traveled 100+ km total",
                "check": lambda: user_activity["total_distance"] >= 100
            },
            "route_master": {
                "name": "Route Master",
                "description": "Tried all route types",
                "check": lambda: len(user_activity["route_types"]) >= 3
            },
            "consistent_user": {
                "name": "Consistent User", 
                "description": "Used SafeRoute for 7+ days",
                "check": lambda: len(user_activity["activity_days"]) >= 7
            }
        }
        
        # Check each achievement
        for achievement_id, achievement in achievements.items():
            if achievement_id not in user_achievements and achievement["check"]():
                user_achievements[achievement_id] = {
                    "name": achievement["name"],
                    "description": achievement["description"], 
                    "earned_date": datetime.now().isoformat(),
                    "earned": True
                }
                logger.info(f"Achievement '{achievement['name']}' earned by user {user_id}")
        
        self._save_achievements()
    
    def get_user_profile_data(self, user_id: str) -> Dict:
        """Get comprehensive profile data for a user."""
        try:
            if user_id not in self.activities:
                return {
                    "personal_stats": {
                        "routes_calculated": 0,
                        "total_distance": "0 km",
                        "safety_score": 0,
                        "time_saved": "0 min"
                    },
                    "recent_routes": [],
                    "achievements": [],
                    "activity_chart_data": self._get_empty_chart_data(),
                    "favorite_route_type": "Balanced",
                    "most_active_day": "N/A",
                    "current_streak": "0 days"
                }
            
            user_activity = self.activities[user_id]
            user_achievements = self.user_achievements.get(user_id, {})
            
            # Calculate personal stats
            routes_count = len(user_activity["routes"])
            total_distance = user_activity["total_distance"]
            avg_safety_score = 0
            if user_activity["safety_scores"]:
                avg_safety_score = sum(user_activity["safety_scores"]) / len(user_activity["safety_scores"])
            
            # Get recent routes (last 5)
            recent_routes = user_activity["routes"][-5:] if user_activity["routes"] else []
            recent_routes.reverse()  # Most recent first
            
            # Format recent routes
            formatted_routes = []
            for route in recent_routes:
                formatted_routes.append({
                    "from": route["from"],
                    "to": route["to"], 
                    "safety_score": self._extract_safety_score(route["safety_score"]) or 0,
                    "date": datetime.fromisoformat(route["timestamp"].replace('Z', '+00:00')).strftime("%Y-%m-%d"),
                    "distance_km": route["distance_km"],
                    "duration_minutes": route["duration_minutes"]
                })
            
            # Get achievements list
            achievement_list = []
            for achievement_data in user_achievements.values():
                achievement_list.append({
                    "name": achievement_data["name"],
                    "description": achievement_data["description"],
                    "earned": True,
                    "earned_date": achievement_data["earned_date"]
                })
            
            # Calculate favorite route type
            favorite_route_type = "Balanced"
            if user_activity["route_types"]:
                favorite_route_type = max(user_activity["route_types"], 
                                        key=user_activity["route_types"].get).title()
            
            # Calculate current streak
            current_streak = self._calculate_current_streak(user_activity["activity_days"])
            
            # Get activity chart data
            chart_data = self._get_activity_chart_data(user_activity["routes"])
            
            return {
                "personal_stats": {
                    "routes_calculated": routes_count,
                    "total_distance": f"{total_distance:.1f} km",
                    "safety_score": round(avg_safety_score, 1),
                    "time_saved": f"{routes_count * 15} min"  # Estimate 15 min saved per route
                },
                "recent_routes": formatted_routes,
                "achievements": achievement_list,
                "activity_chart_data": chart_data,
                "favorite_route_type": favorite_route_type,
                "most_active_day": self._get_most_active_day(user_activity["routes"]),
                "current_streak": f"{current_streak} days"
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile data: {e}")
            return self.get_user_profile_data("nonexistent")  # Return empty data
    
    def _calculate_current_streak(self, activity_days: List[str]) -> int:
        """Calculate current consecutive activity streak."""
        if not activity_days:
            return 0
        
        # Sort dates
        sorted_dates = sorted([datetime.fromisoformat(d).date() for d in activity_days])
        current_date = datetime.now().date()
        streak = 0
        
        # Count backwards from today
        check_date = current_date
        for _ in range(30):  # Check up to 30 days back
            if check_date.isoformat() in activity_days:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _get_most_active_day(self, routes: List[Dict]) -> str:
        """Get the most active day of the week."""
        if not routes:
            return "N/A"
        
        day_counts = defaultdict(int)
        for route in routes:
            date = datetime.fromisoformat(route["timestamp"].replace('Z', '+00:00'))
            day_name = date.strftime("%A")
            day_counts[day_name] += 1
        
        if not day_counts:
            return "N/A"
        
        return max(day_counts, key=day_counts.get)
    
    def _get_activity_chart_data(self, routes: List[Dict]) -> Dict:
        """Generate chart data for the last 7 days."""
        # Get last 7 days
        end_date = datetime.now().date()
        dates = [(end_date - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        
        # Count routes per day
        daily_counts = {date: 0 for date in dates}
        daily_safety = {date: [] for date in dates}
        daily_distance = {date: 0 for date in dates}
        
        for route in routes:
            route_date = datetime.fromisoformat(route["timestamp"].replace('Z', '+00:00')).date().isoformat()
            if route_date in daily_counts:
                daily_counts[route_date] += 1
                
                safety_score = self._extract_safety_score(route["safety_score"])
                if safety_score:
                    daily_safety[route_date].append(safety_score)
                
                if isinstance(route["distance_km"], (int, float)):
                    daily_distance[route_date] += route["distance_km"]
        
        # Calculate average safety per day
        daily_avg_safety = {}
        for date, scores in daily_safety.items():
            daily_avg_safety[date] = sum(scores) / len(scores) if scores else 0
        
        return {
            "dates": [datetime.fromisoformat(d).strftime("Day %d") for d in dates],
            "routes": [daily_counts[d] for d in dates],
            "safety": [daily_avg_safety[d] for d in dates],
            "distance": [daily_distance[d] for d in dates]
        }
    
    def _get_empty_chart_data(self) -> Dict:
        """Return empty chart data structure."""
        return {
            "dates": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
            "routes": [0, 0, 0, 0, 0, 0, 0],
            "safety": [0, 0, 0, 0, 0, 0, 0],
            "distance": [0, 0, 0, 0, 0, 0, 0]
        }

# Global instance
user_activity_service = UserActivityService()