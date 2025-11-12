"""
SafeRoute Navigator v2.0 - Hotspot Service
Demo safety hotspot service with comprehensive functionality.
No external API dependencies - all data generated locally.
"""

import random
import math
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from src.ml.ml_service import ml_service
from src.services.weather_service import weather_service

logger = logging.getLogger(__name__)

class HotspotService:
    """Demo hotspot service with realistic safety data and Google Maps integration."""
    
    def __init__(self, google_maps_service=None, traffic_generator=None):
        """Initialize the hotspot service."""
        self.enabled = True
        self.google_maps_service = google_maps_service
        self.traffic_generator = traffic_generator
        self.google_maps_patterns = {}
        self.demo_traffic_data = {}
        
        # Load Google Maps patterns if available
        self._load_google_maps_data()
        
        # Load enhanced dataset hotspots (149 cities)
        self.base_hotspots = self._load_enhanced_hotspots()
        
        logger.info(f"✅ Hotspot Service initialized with {len(self.base_hotspots)} hotspots from enhanced dataset")
        
        # Hotspot type configurations
        self.hotspot_types = {
            "traffic_congestion": {
                "base_risk": 0.6,
                "color": "#FF9500",
                "priority": "medium",
                "descriptions": [
                    "Heavy traffic congestion during peak hours",
                    "Frequent traffic jams and slow-moving vehicles",
                    "High vehicle density causing significant delays",
                    "Multiple lane merging causing bottlenecks"
                ]
            },
            "accident_prone": {
                "base_risk": 0.8,
                "color": "#FF4444",
                "priority": "high",
                "descriptions": [
                    "High accident frequency zone with poor visibility",
                    "Sharp turns and dangerous road conditions",
                    "Multiple collision incidents reported monthly",
                    "Speeding violations and reckless driving common"
                ]
            },
            "construction": {
                "base_risk": 0.7,
                "color": "#FFAA00",
                "priority": "medium",
                "descriptions": [
                    "Ongoing construction work affecting traffic flow",
                    "Lane closures and temporary diversions",
                    "Heavy machinery and worker safety zones",
                    "Infrastructure development causing delays"
                ]
            },
            "flooding_risk": {
                "base_risk": 0.9,
                "color": "#0066FF",
                "priority": "critical",
                "descriptions": [
                    "Prone to waterlogging during monsoon season",
                    "Poor drainage system causing flood risks",
                    "Seasonal flooding affects traffic severely",
                    "Vehicle breakdown risk in flooded areas"
                ]
            },
            "weather_risk": {
                "base_risk": 0.5,
                "color": "#888888",
                "priority": "low",
                "descriptions": [
                    "Weather-dependent visibility issues",
                    "Fog and rain affect driving conditions",
                    "Variable weather conditions impact safety",
                    "Seasonal weather hazards reported"
                ]
            },
            "pedestrian_risk": {
                "base_risk": 0.7,
                "color": "#FF6600",
                "priority": "high",
                "descriptions": [
                    "High pedestrian activity with safety concerns",
                    "Busy market area with heavy foot traffic",
                    "School and college zones with crossing risks",
                    "Inadequate pedestrian infrastructure"
                ]
            }
        }
        
    def _load_enhanced_hotspots(self):
        """Load hotspots from enhanced dataset (149 cities)."""
        import os
        import pandas as pd
        
        hotspots = []
        dataset_file = os.path.join('data', 'enhanced_hotspot_dataset.csv')
        
        try:
            if os.path.exists(dataset_file):
                logger.info("Loading enhanced hotspot dataset...")
                df = pd.read_csv(dataset_file)
                
                # Convert dataset to hotspot format
                risk_types = ['accident_prone', 'traffic_congestion', 'construction', 'flooding_risk', 'weather_risk', 'pedestrian_risk']
                
                for idx, row in df.iterrows():
                    # Determine hotspot type based on characteristics
                    hotspot_type = risk_types[int(row['weather_condition_numeric']) % len(risk_types)]
                    
                    # Override type for specific conditions
                    if row.get('coastal', 0) == 1 and row.get('tsunami_risk', 0) > 0.5:
                        hotspot_type = 'flooding_risk'  # Tsunami/flood risk
                    elif row.get('seismic_zone_risk', 0) > 0.8:
                        hotspot_type = 'accident_prone'  # Earthquake zone
                    elif row.get('traffic_density', 0) > 0.7:
                        hotspot_type = 'traffic_congestion'
                    
                    hotspot = {
                        'city': row['city'],
                        'state': row.get('state', 'Unknown'),
                        'lat': row['latitude'],
                        'lng': row['longitude'],
                        'name': f"{row['city']} - Zone {idx % 10 + 1}",
                        'type': hotspot_type,
                        'risk_level': row['risk_level'],
                        'severity_level': row.get('severity_level', row['risk_level']),
                        'seismic_zone': row.get('seismic_zone', 2),
                        'coastal': bool(row.get('coastal', 0)),
                        'earthquake_risk': row.get('earthquake_risk', 0),
                        'tsunami_risk': row.get('tsunami_risk', 0)
                    }
                    hotspots.append(hotspot)
                
                logger.info(f"Loaded {len(hotspots)} hotspots from enhanced dataset")
                return hotspots
            else:
                logger.warning(f"Enhanced dataset not found at {dataset_file}, using fallback data")
                return self._get_fallback_hotspots()
                
        except Exception as e:
            logger.error(f"Error loading enhanced hotspots: {str(e)}")
            return self._get_fallback_hotspots()
    
    def _get_fallback_hotspots(self):
        """Fallback hotspots if enhanced dataset not available."""
        return [
            # Delhi NCR
            {"city": "Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090, "name": "Connaught Place", "type": "traffic_congestion"},
            {"city": "Delhi", "state": "Delhi", "lat": 28.5355, "lng": 77.3910, "name": "Noida Expressway", "type": "accident_prone"},
            # Mumbai
            {"city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777, "name": "Mumbai Central", "type": "traffic_congestion"},
            {"city": "Mumbai", "state": "Maharashtra", "lat": 19.2183, "lng": 72.9781, "name": "Andheri East", "type": "flooding_risk"},
            # Bangalore
            {"city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946, "name": "MG Road", "type": "traffic_congestion"},
        ]
    
    def add_incident_report(self, incident: Dict):
        """Add reported incident to hotspot tracking for dynamic updates."""
        try:
            logger.info(f"Processing incident report: {incident.get('type')} at ({incident.get('latitude')}, {incident.get('longitude')})")
            # In a full implementation, this would:
            # 1. Check if incident is near existing hotspot
            # 2. Update hotspot risk scores
            # 3. Trigger ML model retraining if needed
            # 4. Create new hotspot if incident cluster detected
            # For now, just log it
            return True
        except Exception as e:
            logger.error(f"Error processing incident report: {e}")
            return False
    
    def _load_google_maps_data(self):
        """Load Google Maps patterns and demo traffic data."""
        try:
            # Load traffic patterns if available
            import os
            patterns_file = os.path.join('data', 'traffic_patterns.json')
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    self.google_maps_patterns = json.load(f)
                logger.info("Google Maps traffic patterns loaded")
            
            # Load demo traffic data if available
            demo_file = os.path.join('data', 'demo_traffic_data.json')
            if os.path.exists(demo_file):
                with open(demo_file, 'r') as f:
                    self.demo_traffic_data = json.load(f)
                logger.info("Demo traffic data loaded")
                
        except Exception as e:
            logger.warning(f"Could not load Google Maps data: {str(e)}")
    
    def update_with_google_maps_data(self, patterns_data: Dict) -> Dict:
        """Update hotspot service with fresh Google Maps data."""
        try:
            self.google_maps_patterns = patterns_data
            
            # Generate new demo data based on patterns
            if self.traffic_generator:
                result = self.traffic_generator.analyze_google_maps_patterns(patterns_data)
                if result['status'] == 'success':
                    self.demo_traffic_data = result['demo_data']
                    logger.info("Hotspot service updated with fresh Google Maps data")
                    return {
                        'status': 'success',
                        'message': 'Hotspot data updated with Google Maps patterns',
                        'patterns_loaded': len(patterns_data.get('patterns', {})),
                        'demo_hotspots_generated': len(self.demo_traffic_data.get('hotspots', []))
                    }
            
            return {
                'status': 'partial',
                'message': 'Google Maps patterns loaded but demo data not generated'
            }
            
        except Exception as e:
            logger.error(f"Failed to update with Google Maps data: {str(e)}")
            return {
                'status': 'error',
                'message': f"Update failed: {str(e)}"
            }
    
    # Initialize hotspot type configurations (moved to __init__)
    def _init_hotspot_types(self):
        """Initialize hotspot type configurations."""
        self.hotspot_types = {
            "traffic_congestion": {
                "base_risk": 0.6,
                "color": "#FF9500",
                "priority": "medium",
                "descriptions": [
                    "Heavy traffic congestion during peak hours",
                    "Frequent traffic jams and slow-moving vehicles",
                    "High vehicle density causing significant delays",
                    "Multiple lane merging causing bottlenecks"
                ]
            },
            "accident_prone": {
                "base_risk": 0.8,
                "color": "#FF4444",
                "priority": "high",
                "descriptions": [
                    "High accident frequency zone with poor visibility",
                    "Sharp turns and dangerous road conditions",
                    "Multiple collision incidents reported monthly",
                    "Speeding violations and reckless driving common"
                ]
            },
            "construction": {
                "base_risk": 0.7,
                "color": "#FFAA00",
                "priority": "medium",
                "descriptions": [
                    "Ongoing construction work affecting traffic flow",
                    "Lane closures and temporary diversions",
                    "Heavy machinery and worker safety zones",
                    "Infrastructure development causing delays"
                ]
            },
            "flooding_risk": {
                "base_risk": 0.9,
                "color": "#0066FF",
                "priority": "critical",
                "descriptions": [
                    "Prone to waterlogging during monsoon season",
                    "Poor drainage system causing flood risks",
                    "Seasonal flooding affects traffic severely",
                    "Vehicle breakdown risk in flooded areas"
                ]
            },
            "weather_risk": {
                "base_risk": 0.5,
                "color": "#888888",
                "priority": "low",
                "descriptions": [
                    "Weather-dependent visibility issues",
                    "Fog and rain affect driving conditions",
                    "Variable weather conditions impact safety",
                    "Seasonal weather hazards reported"
                ]
            },
            "pedestrian_risk": {
                "base_risk": 0.7,
                "color": "#FF6600",
                "priority": "high",
                "descriptions": [
                    "High pedestrian activity with safety concerns",
                    "Busy market area with heavy foot traffic",
                    "School and college zones with crossing risks",
                    "Inadequate pedestrian infrastructure"
                ]
            }
        }
    
    def get_hotspots(self, center_lat: float = None, center_lng: float = None,
                     radius_km: float = 50, risk_filter: str = None,
                     limit: int = 100) -> Dict:
        """
        Get safety hotspots with filtering options.
        
        Args:
            center_lat: Center latitude for radius filtering
            center_lng: Center longitude for radius filtering  
            radius_km: Search radius in kilometers
            risk_filter: Risk level filter ('low', 'medium', 'high', 'critical')
            limit: Maximum number of hotspots to return
            
        Returns:
            Dict with hotspot data
        """
        try:
            hotspots = []
            
            # First, add Google Maps derived hotspots if available
            if self.demo_traffic_data and 'hotspots' in self.demo_traffic_data:
                for gm_hotspot in self.demo_traffic_data['hotspots']:
                    # Filter by radius if center provided
                    if center_lat is not None and center_lng is not None:
                        distance = self._calculate_distance(
                            center_lat, center_lng, 
                            gm_hotspot['latitude'], gm_hotspot['longitude']
                        )
                        if distance > radius_km:
                            continue
                    
                    # Filter by risk level if specified
                    if risk_filter and gm_hotspot.get('risk_level') != risk_filter:
                        continue
                    
                    hotspots.append(gm_hotspot)
            
            # Then process base hotspots
            for base_hotspot in self.base_hotspots:
                # Add coordinate variation for realism
                lat_var = random.uniform(-0.02, 0.02)
                lng_var = random.uniform(-0.02, 0.02)
                
                lat = base_hotspot["lat"] + lat_var
                lng = base_hotspot["lng"] + lng_var
                
                # Filter by radius if center provided
                if center_lat is not None and center_lng is not None:
                    distance = self._calculate_distance(center_lat, center_lng, lat, lng)
                    if distance > radius_km:
                        continue
                
                # Generate dynamic hotspot data
                hotspot_data = self._generate_hotspot_data(base_hotspot, lat, lng)
                
                # Filter by risk level if specified
                if risk_filter and hotspot_data["risk_level"] != risk_filter:
                    continue
                
                hotspots.append(hotspot_data)
            
            # Add random hotspots for variety
            if center_lat and center_lng:
                random_hotspots = self._generate_random_hotspots(
                    center_lat, center_lng, radius_km, min(20, limit - len(hotspots))
                )
                hotspots.extend(random_hotspots)
            
            # Sort by risk score (highest first)
            hotspots.sort(key=lambda x: x["risk_score"], reverse=True)
            
            # Limit results
            hotspots = hotspots[:limit]
            
            return {
                "status": "success",
                "data": {
                    "hotspots": hotspots,
                    "count": len(hotspots),
                    "center": [center_lat, center_lng] if center_lat else None,
                    "radius_km": radius_km,
                    "risk_filter": risk_filter,
                    "generated_at": datetime.utcnow().isoformat()
                },
                "metadata": {
                    "provider": "SafeRoute Demo Hotspot Service",
                    "data_source": "demo_data",
                    "update_frequency": "real-time"
                }
            }
            
        except Exception as e:
            logger.error(f"Hotspot retrieval error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to retrieve hotspots: {str(e)}"
            }
    
    def get_personalized_hotspots(self, user_lat: float, user_lng: float,
                                 radius_km: float = 25, user_preferences: Dict = None) -> Dict:
        """
        Get personalized hotspots based on user location and preferences.
        
        Args:
            user_lat: User's latitude
            user_lng: User's longitude  
            radius_km: Search radius
            user_preferences: User preferences (risk tolerance, route types, etc.)
            
        Returns:
            Dict with personalized hotspot data
        """
        try:
            # Get base hotspots around user
            base_result = self.get_hotspots(user_lat, user_lng, radius_km)
            
            if base_result["status"] != "success":
                return base_result
            
            hotspots = base_result["data"]["hotspots"]
            
            # Apply personalization
            for hotspot in hotspots:
                distance = self._calculate_distance(
                    user_lat, user_lng,
                    hotspot["latitude"], hotspot["longitude"]
                )
                
                # Add distance-based priority
                if distance < 5:
                    hotspot["personal_priority"] = "immediate"
                    hotspot["risk_score"] = min(1.0, hotspot["risk_score"] * 1.2)
                elif distance < 15:
                    hotspot["personal_priority"] = "high" 
                else:
                    hotspot["personal_priority"] = "medium"
                
                hotspot["distance_km"] = round(distance, 1)
                hotspot["eta_minutes"] = round(distance / 40 * 60, 1)  # Assume 40 km/h avg speed
                
                # User preference adjustments
                if user_preferences:
                    risk_tolerance = user_preferences.get("risk_tolerance", "medium")
                    if risk_tolerance == "low" and hotspot["risk_score"] > 0.6:
                        hotspot["recommendation"] = "strongly_avoid"
                    elif risk_tolerance == "high" and hotspot["risk_score"] < 0.4:
                        hotspot["recommendation"] = "acceptable"
                    else:
                        hotspot["recommendation"] = "caution_advised"
            
            # Sort by personal priority and distance
            priority_order = {"immediate": 0, "high": 1, "medium": 2}
            hotspots.sort(key=lambda x: (priority_order.get(x["personal_priority"], 3), x["distance_km"]))
            
            return {
                "status": "success",
                "data": {
                    "hotspots": hotspots,
                    "count": len(hotspots),
                    "user_location": [user_lat, user_lng],
                    "personalization_applied": True,
                    "generated_at": datetime.utcnow().isoformat()
                },
                "metadata": {
                    "provider": "SafeRoute Personalized Hotspot Service",
                    "personalization_factors": ["distance", "user_preferences", "risk_tolerance"],
                    "recommendation_engine": "demo_ml_model"
                }
            }
            
        except Exception as e:
            logger.error(f"Personalized hotspot error: {str(e)}")
            return {
                "status": "error", 
                "message": f"Failed to get personalized hotspots: {str(e)}"
            }
    
    def _generate_hotspot_data(self, base_hotspot: Dict, lat: float, lng: float) -> Dict:
        """Generate detailed hotspot data using ML predictions and real weather data."""
        hotspot_type = base_hotspot["type"]
        type_config = self.hotspot_types[hotspot_type]
        
        # Get real weather data for the location
        weather_data = weather_service.get_current_weather(lat, lng)
        
        # Prepare data for ML prediction
        location_data = {
            'weather': weather_data.get('data', {}).get('current', {}),
            'road_type': self._infer_road_type(base_hotspot["name"]),
            'traffic_density': self._estimate_traffic_density(lat, lng),
            'location': {'latitude': lat, 'longitude': lng}
        }
        
        # Get ML-powered risk prediction
        ml_prediction = ml_service.predict_hotspot_risk(location_data)
        
        if ml_prediction.get('status') == 'success':
            predictions = ml_prediction.get('predictions', {})
            risk_data = predictions.get('risk', {})
            risk_score = risk_data.get('probability', 0.5)
            risk_level = risk_data.get('risk_level', 'medium')
            ml_confidence = risk_data.get('confidence', 0.7)
            logger.info(f"ML prediction for {base_hotspot['name']}: {risk_level} ({risk_score:.2f})")
        else:
            # Fallback to enhanced rule-based prediction if ML fails
            risk_score, risk_level = self._calculate_enhanced_risk(base_hotspot, weather_data)
            ml_confidence = 0.6
            logger.info(f"ML model unavailable for {base_hotspot['name']}, using rule-based fallback")
        
        # Generate incident data
        incidents = self._generate_recent_incidents(lat, lng, hotspot_type)
        
        return {
            "id": f"hotspot_{hash(base_hotspot['name'] + str(lat) + str(lng)) % 100000}",
            "latitude": round(lat, 6),
            "longitude": round(lng, 6),
            "name": base_hotspot["name"],
            "city": base_hotspot["city"],
            "type": hotspot_type,
            "description": random.choice(type_config["descriptions"]),
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "priority": type_config["priority"],
            "color": type_config["color"],
            "affected_radius_m": random.randint(100, 500),
            "severity": self._get_severity_from_risk(risk_score),
            "incident_count_24h": random.randint(1, 15),
            "avg_delay_minutes": random.randint(3, 25),
            "confidence": random.uniform(0.7, 0.95),
            "last_updated": (datetime.utcnow() - timedelta(minutes=random.randint(1, 120))).isoformat(),
            "verified": random.choice([True, False]),
            "source": "demo_sensors",
            "active": True,
            "weather_dependent": hotspot_type in ["flooding_risk", "weather_risk"],
            "time_dependent": hotspot_type in ["traffic_congestion", "pedestrian_risk"],
            "recent_incidents": incidents,
            "mitigation_suggestions": self._get_mitigation_suggestions(hotspot_type)
        }
    
    def _generate_random_hotspots(self, center_lat: float, center_lng: float,
                                 radius_km: float, count: int) -> List[Dict]:
        """Generate random hotspots around center point within India bounds."""
        random_hotspots = []
        
        def in_india(lat: float, lng: float) -> bool:
            return 6.5 <= lat <= 35.5 and 68.0 <= lng <= 97.5
        
        attempts = 0
        while len(random_hotspots) < count and attempts < count * 5:
            attempts += 1
            # Generate random point within radius
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(1, radius_km)
            
            # Convert to lat/lng offset
            lat_offset = distance * math.cos(angle) / 111.0
            lng_offset = distance * math.sin(angle) / (111.0 * math.cos(math.radians(center_lat)))
            
            lat = center_lat + lat_offset
            lng = center_lng + lng_offset
            
            if not in_india(lat, lng):
                continue
            
            # Random hotspot properties
            hotspot_type = random.choice(list(self.hotspot_types.keys()))
            type_config = self.hotspot_types[hotspot_type]
            
            risk_score = random.uniform(0.2, 0.9)
            
            random_hotspots.append({
                "id": f"random_hotspot_{len(random_hotspots)}_{random.randint(10000, 99999)}",
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "name": f"Hotspot #{len(random_hotspots)+1}",
                "city": "Unknown",
                "type": hotspot_type,
                "description": random.choice(type_config["descriptions"]),
                "risk_score": round(risk_score, 2),
                "risk_level": self._get_risk_level(risk_score),
                "priority": type_config["priority"],
                "color": type_config["color"],
                "affected_radius_m": random.randint(50, 300),
                "severity": self._get_severity_from_risk(risk_score),
                "incident_count_24h": random.randint(0, 10),
                "avg_delay_minutes": random.randint(1, 15),
                "confidence": random.uniform(0.5, 0.8),
                "last_updated": (datetime.utcnow() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                "verified": random.choice([True, False]),
                "source": "crowdsourced",
                "active": True,
                "weather_dependent": hotspot_type in ["flooding_risk", "weather_risk"],
                "time_dependent": hotspot_type in ["traffic_congestion", "pedestrian_risk"],
                "recent_incidents": [],
                "mitigation_suggestions": self._get_mitigation_suggestions(hotspot_type)
            })
        
        return random_hotspots
    
    def _generate_recent_incidents(self, lat: float, lng: float, hotspot_type: str) -> List[Dict]:
        """Generate recent incidents for a hotspot."""
        incidents = []
        num_incidents = random.randint(0, 5)
        
        incident_types = {
            "traffic_congestion": ["traffic_jam", "vehicle_breakdown", "road_rage"],
            "accident_prone": ["collision", "vehicle_accident", "hit_and_run"],
            "construction": ["equipment_failure", "worker_injury", "material_spill"],
            "flooding_risk": ["waterlogging", "vehicle_stuck", "drainage_overflow"],
            "weather_risk": ["visibility_issue", "weather_hazard", "storm_damage"],
            "pedestrian_risk": ["pedestrian_accident", "crowd_gathering", "street_vendor_blocking"]
        }
        
        relevant_incidents = incident_types.get(hotspot_type, ["general_incident"])
        
        for i in range(num_incidents):
            incident_time = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            
            incidents.append({
                "id": f"incident_{random.randint(100000, 999999)}",
                "type": random.choice(relevant_incidents),
                "severity": random.choice(["minor", "moderate", "severe"]),
                "description": f"{random.choice(relevant_incidents).replace('_', ' ').title()} reported",
                "location": {"latitude": lat, "longitude": lng},
                "reported_at": incident_time.isoformat(),
                "status": random.choice(["active", "resolved", "investigating"]),
                "impact": random.choice(["low", "medium", "high"])
            })
        
        return incidents
    
    def _get_mitigation_suggestions(self, hotspot_type: str) -> List[str]:
        """Get mitigation suggestions for hotspot type."""
        suggestions = {
            "traffic_congestion": [
                "Use alternative routes during peak hours",
                "Consider carpooling or public transport",
                "Allow extra travel time",
                "Check real-time traffic before departure"
            ],
            "accident_prone": [
                "Reduce speed and maintain safe distance",
                "Avoid overtaking in this zone",
                "Use headlights during daytime",
                "Stay alert for sudden lane changes"
            ],
            "construction": [
                "Follow temporary signage carefully",
                "Reduce speed in construction zones",
                "Maintain safe distance from work vehicles",
                "Be patient with delays"
            ],
            "flooding_risk": [
                "Avoid travel during heavy rainfall",
                "Check weather conditions before departure",
                "Use higher ground routes when possible",
                "Keep emergency supplies in vehicle"
            ],
            "weather_risk": [
                "Monitor weather conditions closely",
                "Use appropriate lighting",
                "Reduce speed in poor visibility",
                "Keep emergency kit ready"
            ],
            "pedestrian_risk": [
                "Drive slowly in populated areas",
                "Watch for pedestrian crossings",
                "Be extra cautious near schools",
                "Use horn sparingly to avoid startling"
            ]
        }
        
        return suggestions.get(hotspot_type, ["Exercise general caution in this area"])
    
    def _infer_road_type(self, location_name: str) -> str:
        """Infer road type from location name."""
        name_lower = location_name.lower()
        
        if any(term in name_lower for term in ['highway', 'expressway', 'nh-', 'nh ', 'national']):
            return 'highway'
        elif any(term in name_lower for term in ['flyover', 'bridge', 'ring road', 'outer']):
            return 'arterial'
        elif any(term in name_lower for term in ['main road', 'mg road', 'brigade']):
            return 'arterial'
        elif any(term in name_lower for term in ['sector', 'phase', 'block', 'colony']):
            return 'collector'
        else:
            return 'arterial'  # Default to arterial for major locations
    
    def _estimate_traffic_density(self, lat: float, lng: float) -> float:
        """Estimate traffic density based on location and time."""
        # Time-based traffic estimation
        hour = datetime.now().hour
        base_density = 0.4  # Base traffic density
        
        # Rush hour adjustments
        if 7 <= hour <= 10 or 17 <= hour <= 20:
            base_density = 0.8  # High density during rush hours
        elif 10 < hour < 17:
            base_density = 0.6  # Moderate density during business hours
        elif 21 <= hour <= 23:
            base_density = 0.5  # Moderate evening traffic
        else:
            base_density = 0.2  # Low density during night/early morning
        
        # Location-based adjustments (simplified)
        # Major metropolitan areas have higher base traffic
        if ((28.4 <= lat <= 28.8 and 77.0 <= lng <= 77.5) or  # Delhi
           (19.0 <= lat <= 19.3 and 72.7 <= lng <= 73.0) or   # Mumbai
           (12.8 <= lat <= 13.1 and 77.4 <= lng <= 77.8)):    # Bangalore
            base_density += 0.1
        
        return min(1.0, base_density)
    
    def _calculate_enhanced_risk(self, base_hotspot: Dict, weather_data: Dict) -> Tuple[float, str]:
        """Calculate enhanced risk score using weather data and location factors."""
        hotspot_type = base_hotspot["type"]
        base_risk = self.hotspot_types[hotspot_type]["base_risk"]
        
        # Weather impact from real data
        weather_impact = 0.0
        if weather_data.get('status') == 'success':
            weather_current = weather_data['data']['current']
            driving_conditions = weather_data['data']['driving_conditions']
            weather_impact = driving_conditions.get('risk_factor', 0.0) * 0.3  # Scale weather impact
        
        # Time-based risk factors
        time_factor = self._get_time_risk_factor()
        
        # Location-specific factors
        location_factor = 0.0
        name_lower = base_hotspot["name"].lower()
        if any(term in name_lower for term in ['junction', 'crossing', 'intersection']):
            location_factor = 0.1
        elif any(term in name_lower for term in ['tunnel', 'bridge', 'flyover']):
            location_factor = 0.15
        elif any(term in name_lower for term in ['highway', 'expressway']):
            location_factor = 0.05
        
        # Combine all factors
        total_risk = base_risk + weather_impact + time_factor + location_factor
        risk_score = max(0.1, min(1.0, total_risk))
        risk_level = self._get_risk_level(risk_score)
        
        return risk_score, risk_level
    
    def _get_time_risk_factor(self) -> float:
        """Get time-based risk factor."""
        hour = datetime.now().hour
        
        # Higher risk during rush hours and night time
        if 22 <= hour or hour <= 5:  # Night hours
            return 0.15
        elif 7 <= hour <= 10 or 17 <= hour <= 20:  # Rush hours
            return 0.1
        elif 10 < hour < 17:  # Business hours
            return 0.05
        else:  # Evening hours
            return 0.08
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level."""
        if risk_score >= 0.8:
            return "very_high"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        elif risk_score >= 0.2:
            return "low"
        else:
            return "very_low"
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    def _get_time_risk_factor(self) -> float:
        """Get risk factor based on current time."""
        hour = datetime.now().hour
        
        if 7 <= hour <= 10 or 17 <= hour <= 20:  # Peak hours
            return 0.2
        elif 22 <= hour or hour <= 5:  # Night hours
            return 0.15
        else:
            return 0.0
    
    def _get_weather_risk_factor(self) -> float:
        """Get random weather risk factor."""
        conditions = ["clear", "cloudy", "light_rain", "heavy_rain", "fog"]
        condition = random.choice(conditions)
        
        risk_factors = {
            "clear": 0.0,
            "cloudy": 0.05,
            "light_rain": 0.15,
            "heavy_rain": 0.25,
            "fog": 0.3
        }
        
        return risk_factors.get(condition, 0.0)
    
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
    
    def _get_severity_from_risk(self, risk_score: float) -> str:
        """Get severity level from risk score."""
        if risk_score >= 0.8:
            return "severe"
        elif risk_score >= 0.6:
            return "moderate"
        else:
            return "minor"

# Global instance
hotspot_service = HotspotService()