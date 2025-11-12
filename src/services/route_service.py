"""
SafeRoute Navigator v2.0 - Route Service
Demo route calculation service with comprehensive functionality.
No external API dependencies - all data generated locally.
"""

import math
import random
import hashlib
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RouteService:
    """Demo route service with realistic route calculation."""
    
    def __init__(self):
        """Initialize the route service."""
        self.enabled = True
        self.cache = {}
        logger.info("✅ Route Service initialized (Demo Mode)")
        
        # Major Indian cities with coordinates
        self.cities = {
            "delhi": {"lat": 28.6139, "lng": 77.2090, "name": "New Delhi"},
            "mumbai": {"lat": 19.0760, "lng": 72.8777, "name": "Mumbai"},
            "bangalore": {"lat": 12.9716, "lng": 77.5946, "name": "Bangalore"},
            "chennai": {"lat": 13.0827, "lng": 80.2707, "name": "Chennai"},
            "kolkata": {"lat": 22.5726, "lng": 88.3639, "name": "Kolkata"},
            "hyderabad": {"lat": 17.3850, "lng": 78.4867, "name": "Hyderabad"},
            "pune": {"lat": 18.5204, "lng": 73.8567, "name": "Pune"},
            "ahmedabad": {"lat": 23.0225, "lng": 72.5714, "name": "Ahmedabad"},
            "jaipur": {"lat": 26.9124, "lng": 75.7873, "name": "Jaipur"},
            "lucknow": {"lat": 26.8467, "lng": 80.9462, "name": "Lucknow"},
            "kanpur": {"lat": 26.4499, "lng": 80.3319, "name": "Kanpur"},
            "nagpur": {"lat": 21.1458, "lng": 79.0882, "name": "Nagpur"},
            "indore": {"lat": 22.7196, "lng": 75.8577, "name": "Indore"},
            "thane": {"lat": 19.2183, "lng": 72.9781, "name": "Thane"},
            "bhopal": {"lat": 23.2599, "lng": 77.4126, "name": "Bhopal"}
        }
        
        # Route type configurations
        self.route_configs = {
            "fastest": {"speed_factor": 1.2, "risk_factor": 1.1, "fuel_factor": 1.15},
            "shortest": {"speed_factor": 0.9, "risk_factor": 0.8, "fuel_factor": 0.9},
            "balanced": {"speed_factor": 1.0, "risk_factor": 1.0, "fuel_factor": 1.0},
            "safest": {"speed_factor": 0.8, "risk_factor": 0.6, "fuel_factor": 0.95},
            "eco": {"speed_factor": 0.85, "risk_factor": 0.9, "fuel_factor": 0.8}
        }
    
    def geocode(self, address: str) -> Dict:
        """
        Convert address to coordinates using demo data.
        
        Args:
            address: Address to geocode
            
        Returns:
            Dict with geocoding results
        """
        try:
            address_clean = address.lower().strip()
            
            # Check if input is already coordinates (lat,lng format)
            if ',' in address_clean:
                try:
                    parts = address_clean.replace(' ', '').split(',')  
                    if len(parts) == 2:
                        lat = float(parts[0])
                        lng = float(parts[1])
                        
                        # Validate coordinates are reasonable for India region
                        if 6.0 <= lat <= 38.0 and 68.0 <= lng <= 98.0:
                            return {
                                "status": "success",
                                "latitude": lat,
                                "longitude": lng,
                                "display_name": f"Location at {lat:.4f}, {lng:.4f}",
                                "city": "Coordinates",
                                "country": "India",
                                "confidence": 1.0,
                                "source": "coordinate_input"
                            }
                except ValueError:
                    pass  # Not valid coordinates, continue with city lookup
            
            # Direct city match
            for city_key, city_info in self.cities.items():
                if city_key in address_clean or city_info["name"].lower() in address_clean:
                    # Add small random variation for realistic behavior
                    lat_var = random.uniform(-0.05, 0.05)
                    lng_var = random.uniform(-0.05, 0.05)
                    
                    return {
                        "status": "success",
                        "latitude": city_info["lat"] + lat_var,
                        "longitude": city_info["lng"] + lng_var,
                        "display_name": f"{city_info['name']}, India",
                        "city": city_info["name"],
                        "country": "India",
                        "confidence": random.uniform(0.85, 0.98),
                        "source": "demo_geocoder"
                    }
            
            # No match found - provide helpful error message
            available_cities = [info["name"] for info in self.cities.values()][:10]
            return {
                "status": "error",
                "message": f"Location '{address}' not recognized. Try coordinates (lat,lng) or one of these cities: {', '.join(available_cities)}",
                "available_cities": available_cities
            }
            
        except Exception as e:
            logger.error(f"Geocoding error: {str(e)}")
            return {
                "status": "error",
                "message": f"Geocoding failed: {str(e)}"
            }
    
    def calculate_route(self, start_location: str, end_location: str, 
                       route_type: str = "balanced") -> Dict:
        """
        Calculate route between two locations.
        
        Args:
            start_location: Starting location
            end_location: Ending location
            route_type: Type of route (fastest, shortest, balanced, safest, eco)
            
        Returns:
            Dict with route calculation results
        """
        try:
            # Check cache
            cache_key = f"{start_location}|{end_location}|{route_type}"
            if cache_key in self.cache:
                cached_result = self.cache[cache_key].copy()
                cached_result["from_cache"] = True
                return cached_result
            
            # Geocode start location
            start_geo = self.geocode(start_location)
            if start_geo["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Could not find starting location: {start_geo.get('message', start_location)}",
                    "available_cities": start_geo.get('available_cities', [])
                }
            
            # Geocode end location
            end_geo = self.geocode(end_location)
            if end_geo["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Could not find destination: {end_geo.get('message', end_location)}",
                    "available_cities": end_geo.get('available_cities', [])
                }
            
            # Calculate route
            route_data = self._calculate_route_data(
                start_geo["latitude"], start_geo["longitude"],
                end_geo["latitude"], end_geo["longitude"],
                route_type
            )
            
            # Build complete response
            result = {
                "status": "success",
                "route": {
                    "distance_km": route_data["distance_km"],
                    "duration_minutes": route_data["duration_minutes"],
                    "traffic_delay_minutes": route_data["traffic_delay_minutes"],
                    "fuel_cost_estimate": route_data["fuel_cost_estimate"],
                    "route_type": route_type,
                    "coordinates": route_data["coordinates"],
                    "waypoints": route_data["waypoints"]
                },
                "start_location": {
                    "input": start_location,
                    "coordinates": [start_geo["latitude"], start_geo["longitude"]],
                    "display_name": start_geo["display_name"]
                },
                "end_location": {
                    "input": end_location,
                    "coordinates": [end_geo["latitude"], end_geo["longitude"]],
                    "display_name": end_geo["display_name"]
                },
                "safety": {
                    "risk_score": route_data["risk_score"],
                    "risk_level": route_data["risk_level"],
                    "safety_rating": route_data["safety_rating"],
                    "risk_factors": route_data["risk_factors"]
                },
                "incidents": route_data["incidents"],
                "weather_impact": route_data["weather_impact"],
                "metadata": {
                    "provider": "SafeRoute Demo Service",
                    "generated_at": datetime.utcnow().isoformat(),
                    "calculation_time_ms": route_data["calculation_time_ms"],
                    "from_cache": False
                }
            }
            
            # Cache result
            self.cache[cache_key] = result.copy()
            
            return result
            
        except Exception as e:
            logger.error(f"Route calculation error: {str(e)}")
            return {
                "status": "error",
                "message": f"Route calculation failed: {str(e)}"
            }
    
    def _calculate_route_data(self, start_lat: float, start_lng: float,
                             end_lat: float, end_lng: float, route_type: str) -> Dict:
        """Calculate detailed route data."""
        start_time = datetime.utcnow()
        
        # Calculate straight-line distance
        direct_distance = self._haversine_distance(start_lat, start_lng, end_lat, end_lng)
        
        # Adjust for road network (roads are typically 1.2-1.4x direct distance)
        route_distance = direct_distance * random.uniform(1.2, 1.4)
        
        # Get route configuration
        config = self.route_configs.get(route_type, self.route_configs["balanced"])
        
        # Calculate duration based on route type and distance
        base_speed = self._get_base_speed(route_distance)
        adjusted_speed = base_speed * config["speed_factor"]
        duration_minutes = (route_distance / adjusted_speed) * 60
        
        # Calculate traffic delays
        traffic_delay = self._calculate_traffic_delay(duration_minutes, start_lat, start_lng)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            route_distance, duration_minutes, route_type, start_lat, start_lng
        ) * config["risk_factor"]
        
        # Generate route coordinates
        coordinates = self._generate_route_coordinates(
            start_lat, start_lng, end_lat, end_lng, route_distance
        )
        
        # Generate waypoints
        waypoints = self._generate_waypoints(coordinates)
        
        # Calculate fuel cost
        fuel_cost = (route_distance * 0.08 * 100) * config["fuel_factor"]  # Rs. 100/L, 8L/100km
        
        # Generate incidents
        incidents = self._generate_route_incidents(coordinates)
        
        # Calculate weather impact
        weather_impact = self._calculate_weather_impact()
        
        # Determine risk level and safety rating
        risk_level = self._get_risk_level(risk_score)
        safety_rating = self._get_safety_rating(risk_score)
        
        calculation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "distance_km": round(route_distance, 2),
            "duration_minutes": round(duration_minutes, 1),
            "traffic_delay_minutes": round(traffic_delay, 1),
            "fuel_cost_estimate": round(fuel_cost, 2),
            "coordinates": coordinates,
            "waypoints": waypoints,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "safety_rating": safety_rating,
            "risk_factors": self._get_risk_factors(risk_score),
            "incidents": incidents,
            "weather_impact": weather_impact,
            "calculation_time_ms": round(calculation_time, 2)
        }
    
    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    def _get_base_speed(self, distance_km: float) -> float:
        """Get base speed based on distance (simulates different road types)."""
        if distance_km < 10:
            return random.uniform(25, 40)  # City roads
        elif distance_km < 100:
            return random.uniform(45, 65)  # State highways
        else:
            return random.uniform(60, 80)  # National highways
    
    def _calculate_traffic_delay(self, base_duration: float, lat: float, lng: float) -> float:
        """Calculate traffic delays based on time and location."""
        current_hour = datetime.now().hour
        
        # Peak hours have more delays
        if 7 <= current_hour <= 10 or 17 <= current_hour <= 20:
            delay_factor = random.uniform(0.2, 0.4)  # 20-40% delay
        elif 10 < current_hour < 17:
            delay_factor = random.uniform(0.1, 0.2)  # 10-20% delay
        else:
            delay_factor = random.uniform(0.05, 0.15)  # 5-15% delay
        
        return base_duration * delay_factor
    
    def _calculate_risk_score(self, distance_km: float, duration_minutes: float,
                             route_type: str, lat: float, lng: float) -> float:
        """Calculate risk score for the route."""
        base_risk = 0.3
        
        # Distance factor
        if distance_km > 500:
            base_risk += 0.2
        elif distance_km > 200:
            base_risk += 0.1
        elif distance_km < 20:
            base_risk += 0.15  # City traffic risks
        
        # Time factor
        current_hour = datetime.now().hour
        if 22 <= current_hour or current_hour <= 5:
            base_risk += 0.2  # Night driving
        elif 7 <= current_hour <= 10 or 17 <= current_hour <= 20:
            base_risk += 0.1  # Rush hour
        
        # Weather factor (simulated)
        weather_risk = random.uniform(0, 0.2)
        
        # Random variation
        random_factor = random.uniform(-0.1, 0.1)
        
        total_risk = base_risk + weather_risk + random_factor
        return max(0.0, min(1.0, total_risk))
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level."""
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.6:
            return "medium"
        elif risk_score < 0.8:
            return "high"
        else:
            return "critical"
    
    def _get_safety_rating(self, risk_score: float) -> str:
        """Get safety rating based on risk score."""
        if risk_score < 0.3:
            return "Excellent"
        elif risk_score < 0.6:
            return "Good"
        elif risk_score < 0.8:
            return "Fair"
        else:
            return "Poor"
    
    def _get_risk_factors(self, risk_score: float) -> List[str]:
        """Get risk factors based on risk score."""
        factors = []
        
        if risk_score > 0.6:
            factors.append("High traffic density")
        if random.random() > 0.7:
            factors.append("Weather conditions")
        if datetime.now().hour < 6 or datetime.now().hour > 22:
            factors.append("Night driving")
        if random.random() > 0.8:
            factors.append("Construction zones")
        if risk_score > 0.7:
            factors.append("Accident-prone areas")
            
        return factors if factors else ["Normal traffic conditions"]
    
    def _generate_route_coordinates(self, start_lat: float, start_lng: float,
                                   end_lat: float, end_lng: float, distance_km: float) -> List[List[float]]:
        """Generate route coordinates."""
        # Determine number of points based on distance
        num_points = max(5, min(20, int(distance_km / 50)))
        coordinates = []
        
        for i in range(num_points + 1):
            progress = i / num_points
            
            # Linear interpolation with curve simulation
            lat = start_lat + (end_lat - start_lat) * progress
            lng = start_lng + (end_lng - start_lng) * progress
            
            # Add curve variation (except for start/end points)
            if 0 < i < num_points:
                curve_factor = math.sin(progress * math.pi) * 0.01
                lat += random.uniform(-curve_factor, curve_factor)
                lng += random.uniform(-curve_factor, curve_factor)
            
            coordinates.append([lng, lat])  # GeoJSON format [lng, lat]
        
        return coordinates
    
    def _generate_waypoints(self, coordinates: List[List[float]]) -> List[Dict]:
        """Generate waypoints along the route."""
        waypoints = []
        total_points = len(coordinates)
        
        # Select waypoints at 25%, 50%, 75% of route
        for percent in [0.25, 0.5, 0.75]:
            index = int(total_points * percent)
            if 0 <= index < total_points:
                coord = coordinates[index]
                waypoints.append({
                    "latitude": coord[1],
                    "longitude": coord[0],
                    "description": f"Waypoint at {percent*100:.0f}% of route",
                    "type": "intermediate"
                })
        
        return waypoints
    
    def _generate_route_incidents(self, coordinates: List[List[float]]) -> List[Dict]:
        """Generate demo incidents along the route."""
        incidents = []
        num_incidents = random.randint(0, 3)
        
        incident_types = [
            {"type": "traffic_jam", "severity": "moderate", "delay": 5},
            {"type": "construction", "severity": "minor", "delay": 3},
            {"type": "accident", "severity": "severe", "delay": 10},
            {"type": "road_closure", "severity": "severe", "delay": 15}
        ]
        
        for i in range(num_incidents):
            incident = random.choice(incident_types)
            coord_index = random.randint(1, len(coordinates) - 2)
            coord = coordinates[coord_index]
            
            incidents.append({
                "id": f"incident_{i}_{random.randint(1000, 9999)}",
                "type": incident["type"],
                "severity": incident["severity"],
                "location": {
                    "latitude": coord[1],
                    "longitude": coord[0]
                },
                "description": f"{incident['type'].replace('_', ' ').title()} reported",
                "delay_minutes": incident["delay"],
                "reported_at": (datetime.utcnow() - timedelta(minutes=random.randint(5, 120))).isoformat(),
                "verified": random.choice([True, False])
            })
        
        return incidents
    
    def _calculate_weather_impact(self) -> Dict:
        """Calculate weather impact on route."""
        conditions = ["clear", "cloudy", "light_rain", "heavy_rain", "fog"]
        current_condition = random.choice(conditions)
        
        impact_levels = {
            "clear": {"impact": "none", "delay_factor": 1.0},
            "cloudy": {"impact": "minimal", "delay_factor": 1.05},
            "light_rain": {"impact": "moderate", "delay_factor": 1.15},
            "heavy_rain": {"impact": "significant", "delay_factor": 1.3},
            "fog": {"impact": "severe", "delay_factor": 1.4}
        }
        
        impact_data = impact_levels[current_condition]
        
        return {
            "condition": current_condition,
            "impact_level": impact_data["impact"],
            "delay_factor": impact_data["delay_factor"],
            "visibility_km": random.randint(1, 10) if current_condition == "fog" else random.randint(8, 15),
            "temperature_c": random.randint(15, 40),
            "humidity_percent": random.randint(30, 90)
        }

# Global instance
route_service = RouteService()