"""
SafeRoute Navigator v2.0 - Traffic Pattern Generator
Generates realistic traffic and hotspot data based on Google Maps API patterns.
Uses strategic sampling to create comprehensive demo data.
"""

import json
import random
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math
import os

logger = logging.getLogger(__name__)

class TrafficPatternGenerator:
    """Generates realistic traffic patterns based on Google Maps data."""
    
    def __init__(self):
        """Initialize the traffic pattern generator."""
        self.patterns = {}
        self.demo_data = {}
        logger.info("🚦 Traffic Pattern Generator initialized")
        
        # Base traffic patterns by location type and time
        self.base_patterns = {
            'city_center': {
                'rush_hour_multiplier': 2.5,
                'daytime_multiplier': 1.8,
                'evening_multiplier': 1.4,
                'night_multiplier': 0.7,
                'base_congestion': 0.6
            },
            'business_district': {
                'rush_hour_multiplier': 3.0,
                'daytime_multiplier': 2.2,
                'evening_multiplier': 1.2,
                'night_multiplier': 0.5,
                'base_congestion': 0.7
            },
            'highway': {
                'rush_hour_multiplier': 2.2,
                'daytime_multiplier': 1.5,
                'evening_multiplier': 1.6,
                'night_multiplier': 0.8,
                'base_congestion': 0.4
            },
            'airport_corridor': {
                'rush_hour_multiplier': 2.0,
                'daytime_multiplier': 1.7,
                'evening_multiplier': 1.8,
                'night_multiplier': 1.0,
                'base_congestion': 0.5
            },
            'residential': {
                'rush_hour_multiplier': 1.8,
                'daytime_multiplier': 1.2,
                'evening_multiplier': 1.3,
                'night_multiplier': 0.6,
                'base_congestion': 0.3
            }
        }
        
        # Incident types and their likelihood by location
        self.incident_patterns = {
            'city_center': {
                'traffic_jam': 0.4,
                'minor_accident': 0.3,
                'road_construction': 0.15,
                'special_event': 0.1,
                'weather_impact': 0.05
            },
            'highway': {
                'traffic_jam': 0.35,
                'minor_accident': 0.4,
                'major_accident': 0.1,
                'road_construction': 0.1,
                'weather_impact': 0.05
            },
            'business_district': {
                'traffic_jam': 0.5,
                'minor_accident': 0.2,
                'parking_issues': 0.15,
                'special_event': 0.1,
                'road_construction': 0.05
            }
        }
    
    def analyze_google_maps_patterns(self, google_maps_data: Dict) -> Dict:
        """
        Analyze Google Maps traffic patterns and generate comprehensive demo data.
        
        Args:
            google_maps_data: Traffic patterns from Google Maps service
            
        Returns:
            Dict containing analyzed patterns and generated demo data
        """
        try:
            logger.info("🔍 Analyzing Google Maps patterns for demo data generation...")
            
            self.patterns = google_maps_data.get('patterns', {})
            
            # Generate comprehensive hotspot data
            hotspots = self._generate_hotspot_data()
            
            # Generate traffic flow patterns
            traffic_flows = self._generate_traffic_flow_data()
            
            # Generate incident patterns
            incidents = self._generate_incident_data()
            
            # Generate route alternatives
            route_alternatives = self._generate_route_alternatives()
            
            self.demo_data = {
                'hotspots': hotspots,
                'traffic_flows': traffic_flows,
                'incidents': incidents,
                'route_alternatives': route_alternatives,
                'generation_timestamp': datetime.utcnow().isoformat(),
                'based_on_google_maps': True,
                'api_calls_used': google_maps_data.get('api_calls_used', 0)
            }
            
            # Save the demo data
            self._save_demo_data()
            
            logger.info(f"✅ Generated comprehensive demo data with {len(hotspots)} hotspots")
            
            return {
                'status': 'success',
                'demo_data': self.demo_data,
                'summary': {
                    'hotspots_generated': len(hotspots),
                    'traffic_flows': len(traffic_flows),
                    'incidents': len(incidents),
                    'route_alternatives': len(route_alternatives)
                }
            }
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {str(e)}")
            return {
                'status': 'error',
                'message': f"Pattern analysis failed: {str(e)}"
            }
    
    def _generate_hotspot_data(self) -> List[Dict]:
        """Generate realistic hotspot data based on traffic patterns."""
        hotspots = []
        
        # Major Indian cities with known traffic hotspots
        city_hotspots = {
            'Delhi': [
                {'name': 'Connaught Place', 'lat': 28.6315, 'lng': 77.2167, 'type': 'city_center'},
                {'name': 'India Gate Circle', 'lat': 28.6129, 'lng': 77.2295, 'type': 'monument'},
                {'name': 'ITO Intersection', 'lat': 28.6269, 'lng': 77.2420, 'type': 'intersection'},
                {'name': 'AIIMS Flyover', 'lat': 28.5672, 'lng': 77.2100, 'type': 'flyover'},
                {'name': 'Dhaula Kuan', 'lat': 28.5955, 'lng': 77.1640, 'type': 'intersection'},
                {'name': 'Lajpat Nagar', 'lat': 28.5653, 'lng': 77.2431, 'type': 'market'},
                {'name': 'Karol Bagh', 'lat': 28.6519, 'lng': 77.1909, 'type': 'market'},
                {'name': 'Rajouri Garden', 'lat': 28.6465, 'lng': 77.1207, 'type': 'market'}
            ],
            'Mumbai': [
                {'name': 'Dadar TT Circle', 'lat': 19.0176, 'lng': 72.8562, 'type': 'intersection'},
                {'name': 'Bandra-Kurla Complex', 'lat': 19.0596, 'lng': 72.8656, 'type': 'business_district'},
                {'name': 'Andheri Link Road', 'lat': 19.1197, 'lng': 72.8464, 'type': 'highway'},
                {'name': 'Marine Drive', 'lat': 18.9448, 'lng': 72.8234, 'type': 'coastal_road'},
                {'name': 'Mahim Causeway', 'lat': 19.0330, 'lng': 72.8397, 'type': 'bridge'},
                {'name': 'Worli Sea Link', 'lat': 19.0176, 'lng': 72.8118, 'type': 'bridge'},
                {'name': 'Powai Hiranandani', 'lat': 19.1197, 'lng': 72.9069, 'type': 'residential'}
            ],
            'Bangalore': [
                {'name': 'Silk Board Junction', 'lat': 12.9165, 'lng': 77.6224, 'type': 'intersection'},
                {'name': 'Electronic City Flyover', 'lat': 12.8456, 'lng': 77.6603, 'type': 'flyover'},
                {'name': 'Whitefield Road', 'lat': 12.9698, 'lng': 77.7500, 'type': 'tech_corridor'},
                {'name': 'Outer Ring Road - Marathahalli', 'lat': 12.9591, 'lng': 77.6974, 'type': 'highway'},
                {'name': 'KR Puram Bridge', 'lat': 12.9924, 'lng': 77.7064, 'type': 'bridge'},
                {'name': 'Hosur Road - Bommanahalli', 'lat': 12.9141, 'lng': 77.6341, 'type': 'highway'}
            ]
        }
        
        for city, locations in city_hotspots.items():
            for location in locations:
                # Generate realistic hotspot data
                congestion_base = self.base_patterns.get(location['type'], self.base_patterns['city_center'])
                
                hotspot = {
                    'id': f"hotspot_{len(hotspots) + 1}",
                    'name': location['name'],
                    'city': city,
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'type': location['type'],
                    'risk_score': self._calculate_risk_score(location['type']),
                    'risk_level': self._classify_risk_level(self._calculate_risk_score(location['type'])),
                    'congestion_patterns': self._generate_time_based_congestion(congestion_base),
                    'incident_history': self._generate_incident_history(location['type']),
                    'safety_features': self._generate_safety_features(),
                    'alternative_routes': self._generate_alternative_routes_count(),
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                hotspots.append(hotspot)
        
        # Add some random hotspots based on Google Maps patterns
        if self.patterns:
            additional_hotspots = self._generate_pattern_based_hotspots()
            hotspots.extend(additional_hotspots)
        
        return hotspots
    
    def _generate_traffic_flow_data(self) -> List[Dict]:
        """Generate traffic flow data for different routes."""
        traffic_flows = []
        
        # Major route corridors
        routes = [
            {'name': 'NH-1 (Delhi-Chandigarh)', 'type': 'highway', 'distance_km': 250},
            {'name': 'Mumbai-Pune Expressway', 'type': 'expressway', 'distance_km': 95},
            {'name': 'Bangalore-Chennai Highway', 'type': 'highway', 'distance_km': 350},
            {'name': 'Delhi Ring Road', 'type': 'ring_road', 'distance_km': 51},
            {'name': 'Mumbai Eastern Express Highway', 'type': 'highway', 'distance_km': 30}
        ]
        
        for route in routes:
            flow_data = {
                'route_name': route['name'],
                'route_type': route['type'],
                'distance_km': route['distance_km'],
                'hourly_flow_patterns': self._generate_hourly_flow_patterns(),
                'average_speed_patterns': self._generate_speed_patterns(),
                'congestion_zones': self._generate_congestion_zones(),
                'weather_impact': self._generate_weather_impact_patterns()
            }
            traffic_flows.append(flow_data)
        
        return traffic_flows
    
    def _generate_incident_data(self) -> List[Dict]:
        """Generate realistic incident data."""
        incidents = []
        
        # Generate incidents for the past 30 days
        for i in range(150):  # About 5 incidents per day
            incident_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            
            # Random location (focusing on Indian cities)
            cities = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata', 'Pune']
            city = random.choice(cities)
            
            # Base coordinates for cities
            city_coords = {
                'Delhi': (28.6139, 77.2090),
                'Mumbai': (19.0760, 72.8777),
                'Bangalore': (12.9716, 77.5946),
                'Chennai': (13.0827, 80.2707),
                'Kolkata': (22.5726, 88.3639),
                'Pune': (18.5204, 73.8567)
            }
            
            base_lat, base_lng = city_coords[city]
            
            incident = {
                'id': f"incident_{i + 1}",
                'type': random.choice(['minor_accident', 'traffic_jam', 'road_construction', 'weather_delay']),
                'severity': random.choice(['low', 'medium', 'high']),
                'latitude': base_lat + random.uniform(-0.1, 0.1),
                'longitude': base_lng + random.uniform(-0.1, 0.1),
                'city': city,
                'description': self._generate_incident_description(),
                'duration_minutes': random.randint(15, 180),
                'affected_radius_km': random.uniform(0.5, 3.0),
                'reported_at': incident_date.isoformat(),
                'resolved_at': (incident_date + timedelta(minutes=random.randint(15, 180))).isoformat(),
                'impact_score': random.uniform(0.3, 0.9)
            }
            
            incidents.append(incident)
        
        return incidents
    
    def _generate_route_alternatives(self) -> List[Dict]:
        """Generate alternative route suggestions."""
        alternatives = []
        
        common_routes = [
            {
                'origin': 'Connaught Place, Delhi',
                'destination': 'IGI Airport, Delhi',
                'primary_route': 'Via NH-8',
                'alternatives': [
                    {'name': 'Via Ring Road', 'extra_time': 15, 'safety_score': 0.8},
                    {'name': 'Via DND Flyway', 'extra_time': 25, 'safety_score': 0.9}
                ]
            },
            {
                'origin': 'Bandra, Mumbai',
                'destination': 'Andheri, Mumbai',
                'primary_route': 'Via Western Express Highway',
                'alternatives': [
                    {'name': 'Via Link Road', 'extra_time': 10, 'safety_score': 0.7},
                    {'name': 'Via SV Road', 'extra_time': 20, 'safety_score': 0.9}
                ]
            }
        ]
        
        for route_set in common_routes:
            alternatives.append({
                'route_id': f"route_{len(alternatives) + 1}",
                'origin': route_set['origin'],
                'destination': route_set['destination'],
                'primary_route': route_set['primary_route'],
                'alternatives': route_set['alternatives'],
                'last_updated': datetime.utcnow().isoformat()
            })
        
        return alternatives
    
    def _calculate_risk_score(self, location_type: str) -> float:
        """Calculate risk score based on location type."""
        risk_mapping = {
            'intersection': random.uniform(0.6, 0.9),
            'city_center': random.uniform(0.5, 0.8),
            'highway': random.uniform(0.4, 0.7),
            'business_district': random.uniform(0.5, 0.8),
            'bridge': random.uniform(0.4, 0.7),
            'market': random.uniform(0.6, 0.9),
            'flyover': random.uniform(0.3, 0.6)
        }
        return risk_mapping.get(location_type, random.uniform(0.4, 0.7))
    
    def _classify_risk_level(self, risk_score: float) -> str:
        """Classify risk level based on score."""
        if risk_score >= 0.8:
            return 'very_high'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _generate_time_based_congestion(self, base_pattern: Dict) -> Dict:
        """Generate hourly congestion patterns."""
        patterns = {}
        for hour in range(24):
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                multiplier = base_pattern['rush_hour_multiplier']
            elif 10 <= hour <= 16:  # Daytime
                multiplier = base_pattern['daytime_multiplier']
            elif 20 <= hour <= 22:  # Evening
                multiplier = base_pattern['evening_multiplier']
            else:  # Night
                multiplier = base_pattern['night_multiplier']
            
            congestion = min(1.0, base_pattern['base_congestion'] * multiplier)
            patterns[f"hour_{hour}"] = round(congestion, 2)
        
        return patterns
    
    def _generate_incident_history(self, location_type: str) -> List[Dict]:
        """Generate incident history for a location."""
        incidents = []
        incident_types = list(self.incident_patterns.get(location_type, self.incident_patterns['city_center']).keys())
        
        for _ in range(random.randint(3, 8)):
            incident = {
                'date': (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
                'type': random.choice(incident_types),
                'severity': random.choice(['low', 'medium', 'high']),
                'duration_minutes': random.randint(30, 240)
            }
            incidents.append(incident)
        
        return incidents
    
    def _generate_safety_features(self) -> List[str]:
        """Generate safety features available at a location."""
        all_features = [
            'traffic_signals', 'speed_cameras', 'cctv_monitoring',
            'police_patrol', 'emergency_services', 'street_lighting',
            'pedestrian_crossing', 'dividers', 'reflective_signs'
        ]
        return random.sample(all_features, random.randint(3, 6))
    
    def _generate_alternative_routes_count(self) -> int:
        """Generate number of alternative routes available."""
        return random.randint(1, 4)
    
    def _generate_pattern_based_hotspots(self) -> List[Dict]:
        """Generate additional hotspots based on Google Maps patterns."""
        hotspots = []
        
        # Extract coordinates from Google Maps patterns if available
        for location_type, locations in self.patterns.items():
            for location_data in locations:
                coords = location_data.get('coordinates', [0, 0])
                if coords[0] != 0 and coords[1] != 0:
                    hotspot = {
                        'id': f"gm_hotspot_{len(hotspots) + 1}",
                        'name': f"Google Maps Derived - {location_data.get('location', 'Unknown')}",
                        'latitude': coords[0],
                        'longitude': coords[1],
                        'type': location_type.replace('_', ''),
                        'risk_score': self._calculate_risk_score(location_type.replace('_', '')),
                        'risk_level': self._classify_risk_level(self._calculate_risk_score(location_type.replace('_', ''))),
                        'google_maps_derived': True,
                        'traffic_data': location_data.get('traffic_data', {}),
                        'last_updated': datetime.utcnow().isoformat()
                    }
                    hotspots.append(hotspot)
        
        return hotspots
    
    def _generate_hourly_flow_patterns(self) -> Dict:
        """Generate hourly traffic flow patterns."""
        patterns = {}
        for hour in range(24):
            # Traffic flow varies by hour
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                flow = random.randint(800, 1200)
            elif 10 <= hour <= 16:  # Daytime
                flow = random.randint(500, 800)
            elif 20 <= hour <= 22:  # Evening
                flow = random.randint(400, 600)
            else:  # Night
                flow = random.randint(100, 400)
            
            patterns[f"hour_{hour}"] = flow
        
        return patterns
    
    def _generate_speed_patterns(self) -> Dict:
        """Generate average speed patterns."""
        patterns = {}
        for hour in range(24):
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                speed = random.randint(20, 35)
            elif 10 <= hour <= 16:  # Daytime
                speed = random.randint(35, 50)
            else:  # Off-peak
                speed = random.randint(45, 65)
            
            patterns[f"hour_{hour}"] = speed
        
        return patterns
    
    def _generate_congestion_zones(self) -> List[Dict]:
        """Generate congestion zone data."""
        zones = []
        for i in range(random.randint(2, 5)):
            zone = {
                'zone_id': f"zone_{i + 1}",
                'start_km': i * 10,
                'end_km': (i + 1) * 10,
                'avg_congestion': random.uniform(0.2, 0.8),
                'peak_congestion': random.uniform(0.6, 1.0)
            }
            zones.append(zone)
        return zones
    
    def _generate_weather_impact_patterns(self) -> Dict:
        """Generate weather impact patterns."""
        return {
            'rain': {'speed_reduction': random.randint(15, 30), 'congestion_increase': random.uniform(0.2, 0.5)},
            'fog': {'speed_reduction': random.randint(25, 45), 'congestion_increase': random.uniform(0.3, 0.6)},
            'storm': {'speed_reduction': random.randint(40, 60), 'congestion_increase': random.uniform(0.5, 0.8)}
        }
    
    def _generate_incident_description(self) -> str:
        """Generate realistic incident descriptions."""
        descriptions = [
            "Minor vehicle breakdown causing lane blockage",
            "Traffic signal malfunction leading to congestion",
            "Road construction work in progress",
            "Minor fender bender between two vehicles",
            "Heavy rainfall causing waterlogging",
            "Special event causing road closures",
            "Emergency vehicle passage causing delays"
        ]
        return random.choice(descriptions)
    
    def _save_demo_data(self) -> None:
        """Save generated demo data to file."""
        try:
            demo_file = os.path.join('data', 'demo_traffic_data.json')
            os.makedirs(os.path.dirname(demo_file), exist_ok=True)
            
            with open(demo_file, 'w') as f:
                json.dump(self.demo_data, f, indent=2, default=str)
                
            logger.info("Demo traffic data saved to file")
        except Exception as e:
            logger.error(f"Failed to save demo data: {str(e)}")
    
    def get_demo_data(self) -> Dict:
        """Get the generated demo data."""
        return self.demo_data