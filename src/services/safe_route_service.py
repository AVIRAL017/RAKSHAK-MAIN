"""
SafeRoute Navigator v2.0 - Safe Route Calculation Service
Calculates safe routes by avoiding traffic hotspots and high-risk areas.
Integrates Google Maps data with ML predictions for optimal route selection.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math
import json

logger = logging.getLogger(__name__)

class SafeRouteService:
    """Service for calculating safe routes avoiding traffic hotspots."""
    
    def __init__(self, google_maps_service=None, hotspot_service=None):
        """Initialize the safe route service."""
        self.google_maps_service = google_maps_service
        self.hotspot_service = hotspot_service
        self.route_cache = {}
        logger.info("🛣️  Safe Route Service initialized")
        
        # Route safety weights
        self.safety_weights = {
            'congestion_factor': 0.3,
            'accident_history': 0.25,
            'weather_impact': 0.15,
            'incident_proximity': 0.2,
            'road_quality': 0.1
        }
        
        # Risk penalty multipliers by type
        self.risk_penalties = {
            'very_high': 2.0,
            'high': 1.5,
            'medium': 1.2,
            'low': 1.0
        }
    
    def calculate_safe_route_from_locations(self, start_location: str, end_location: str,
                                          route_type: str = 'safest',
                                          route_preferences: Optional[Dict] = None) -> Dict:
        """
        Calculate safe route between two string locations (addresses or city names).
        
        Args:
            start_location: Starting location (address, city name, or coordinates)
            end_location: Ending location (address, city name, or coordinates)
            route_type: Type of route calculation
            route_preferences: User preferences for route calculation
            
        Returns:
            Dict containing safe route recommendation
        """
        try:
            # First, we need to geocode the locations
            from .route_service import RouteService
            route_service = RouteService()
            
            # Geocode start location
            start_geo = route_service.geocode(start_location)
            if start_geo['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f"Could not find starting location: {start_geo.get('message', start_location)}",
                    'available_cities': start_geo.get('available_cities', [])
                }
            
            # Geocode end location
            end_geo = route_service.geocode(end_location)
            if end_geo['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f"Could not find destination: {end_geo.get('message', end_location)}",
                    'available_cities': end_geo.get('available_cities', [])
                }
            
            # Now call the main safe route calculation with coordinates
            result = self.calculate_safe_route(
                start_geo['latitude'], start_geo['longitude'],
                end_geo['latitude'], end_geo['longitude'],
                route_preferences
            )
            
            # Add location information to the result
            if result['status'] == 'success':
                result['start_location'] = {
                    'input': start_location,
                    'resolved': start_geo['display_name'],
                    'coordinates': [start_geo['latitude'], start_geo['longitude']]
                }
                result['end_location'] = {
                    'input': end_location,
                    'resolved': end_geo['display_name'],
                    'coordinates': [end_geo['latitude'], end_geo['longitude']]
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Safe route calculation from locations failed: {str(e)}")
            return {
                'status': 'error',
                'message': f"Safe route calculation failed: {str(e)}"
            }
    
    def calculate_safe_route(self, origin_lat: float, origin_lng: float,
                           dest_lat: float, dest_lng: float,
                           route_preferences: Optional[Dict] = None) -> Dict:
        """
        Calculate the safest route between two points.
        
        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            route_preferences: User preferences for route calculation
            
        Returns:
            Dict containing safe route recommendation
        """
        try:
            logger.info(f"Calculating safe route from ({origin_lat}, {origin_lng}) to ({dest_lat}, {dest_lng})")
            
            # Default preferences
            preferences = route_preferences or {
                'avoid_high_risk': True,
                'prioritize_safety': True,
                'max_extra_time': 30,  # minutes
                'avoid_construction': True,
                'prefer_highways': False
            }
            
            # Get primary route from Google Maps
            primary_route = None
            if self.google_maps_service:
                primary_route = self.google_maps_service.get_directions_with_traffic(
                    origin_lat, origin_lng, dest_lat, dest_lng
                )
            
            # Get nearby hotspots
            hotspots = []
            if self.hotspot_service:
                hotspot_data = self.hotspot_service.get_hotspots(
                    origin_lat, origin_lng, 
                    radius_km=self._calculate_search_radius(origin_lat, origin_lng, dest_lat, dest_lng)
                )
                if hotspot_data['status'] == 'success':
                    hotspots = hotspot_data['data']['hotspots']
            
            # Calculate route safety scores
            route_options = self._generate_route_options(
                origin_lat, origin_lng, dest_lat, dest_lng,
                primary_route, hotspots, preferences
            )
            
            # Select the safest route
            best_route = self._select_safest_route(route_options, preferences)
            
            # Generate route recommendations
            recommendations = self._generate_route_recommendations(
                best_route, hotspots, preferences
            )
            
            return {
                'status': 'success',
                'safe_route': best_route,
                'alternatives': route_options[1:4] if len(route_options) > 1 else [],
                'safety_analysis': {
                    'overall_safety_score': best_route.get('safety_score', 0.5),
                    'risk_factors': best_route.get('risk_factors', []),
                    'hotspots_avoided': len([h for h in hotspots if h['risk_level'] in ['high', 'very_high']]),
                    'total_hotspots_nearby': len(hotspots)
                },
                'recommendations': recommendations,
                'calculation_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Safe route calculation failed: {str(e)}")
            return {
                'status': 'error',
                'message': f"Safe route calculation failed: {str(e)}"
            }
    
    def _generate_route_options(self, origin_lat: float, origin_lng: float,
                               dest_lat: float, dest_lng: float,
                               primary_route: Optional[Dict], hotspots: List[Dict],
                               preferences: Dict) -> List[Dict]:
        """Generate multiple route options with safety analysis."""
        route_options = []
        
        # Primary route (direct)
        if primary_route and primary_route['status'] == 'success':
            route_data = primary_route['route_data']
            safety_score = self._calculate_route_safety_score(
                origin_lat, origin_lng, dest_lat, dest_lng,
                route_data, hotspots, 'direct'
            )
            
            route_option = {
                'route_type': 'primary',
                'name': 'Direct Route',
                'distance_km': route_data.get('distance_meters', 0) / 1000,
                'duration_minutes': route_data.get('duration_traffic_seconds', 0) / 60,
                'safety_score': safety_score['overall_score'],
                'risk_factors': safety_score['risk_factors'],
                'congestion_level': route_data.get('congestion_level', 'moderate'),
                'route_data': route_data,
                'recommended': safety_score['overall_score'] >= 0.7
            }
            route_options.append(route_option)
        
        # Generate alternative routes
        alternatives = self._generate_alternative_routes(
            origin_lat, origin_lng, dest_lat, dest_lng, hotspots, preferences
        )
        route_options.extend(alternatives)
        
        # Sort by safety score
        route_options.sort(key=lambda x: x['safety_score'], reverse=True)
        
        return route_options
    
    def _generate_alternative_routes(self, origin_lat: float, origin_lng: float,
                                   dest_lat: float, dest_lng: float,
                                   hotspots: List[Dict], preferences: Dict) -> List[Dict]:
        """Generate alternative route options."""
        alternatives = []
        
        # Alternative 1: Highway-preferred route
        if not preferences.get('prefer_highways', False):
            highway_route = self._simulate_highway_route(
                origin_lat, origin_lng, dest_lat, dest_lng, hotspots
            )
            alternatives.append(highway_route)
        
        # Alternative 2: Hotspot-avoiding route
        avoiding_route = self._simulate_hotspot_avoiding_route(
            origin_lat, origin_lng, dest_lat, dest_lng, hotspots
        )
        alternatives.append(avoiding_route)
        
        # Alternative 3: Time-optimized safe route
        time_optimized_route = self._simulate_time_optimized_safe_route(
            origin_lat, origin_lng, dest_lat, dest_lng, hotspots
        )
        alternatives.append(time_optimized_route)
        
        return alternatives
    
    def _simulate_highway_route(self, origin_lat: float, origin_lng: float,
                               dest_lat: float, dest_lng: float,
                               hotspots: List[Dict]) -> Dict:
        """Simulate a highway-preferred route."""
        distance = self._calculate_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Highway routes are typically 10-20% longer but faster
        highway_distance = distance * 1.15
        highway_time = highway_distance * 1.2  # Assuming 50 km/h average
        
        safety_score = self._calculate_route_safety_score(
            origin_lat, origin_lng, dest_lat, dest_lng,
            {'distance_meters': highway_distance * 1000, 'congestion_level': 'light'},
            hotspots, 'highway'
        )
        
        return {
            'route_type': 'highway',
            'name': 'Highway Route',
            'distance_km': highway_distance,
            'duration_minutes': highway_time,
            'safety_score': safety_score['overall_score'] + 0.1,  # Highways generally safer
            'risk_factors': safety_score['risk_factors'],
            'congestion_level': 'light',
            'extra_distance_km': highway_distance - distance,
            'recommended': safety_score['overall_score'] >= 0.6
        }
    
    def _simulate_hotspot_avoiding_route(self, origin_lat: float, origin_lng: float,
                                       dest_lat: float, dest_lng: float,
                                       hotspots: List[Dict]) -> Dict:
        """Simulate a route that specifically avoids hotspots."""
        distance = self._calculate_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Count high-risk hotspots near the direct route
        high_risk_hotspots = [h for h in hotspots if h['risk_level'] in ['high', 'very_high']]
        
        # Avoiding hotspots adds distance but improves safety
        avoidance_factor = 1.0 + (len(high_risk_hotspots) * 0.05)  # 5% per high-risk hotspot
        avoiding_distance = distance * avoidance_factor
        avoiding_time = avoiding_distance * 1.5  # Slower due to detours
        
        safety_score = self._calculate_route_safety_score(
            origin_lat, origin_lng, dest_lat, dest_lng,
            {'distance_meters': avoiding_distance * 1000, 'congestion_level': 'moderate'},
            [], 'avoiding'  # Empty hotspots as we're avoiding them
        )
        
        return {
            'route_type': 'avoiding',
            'name': 'Hotspot Avoiding Route',
            'distance_km': avoiding_distance,
            'duration_minutes': avoiding_time,
            'safety_score': safety_score['overall_score'] + 0.2,  # Bonus for avoiding hotspots
            'risk_factors': [],
            'congestion_level': 'moderate',
            'hotspots_avoided': len(high_risk_hotspots),
            'extra_distance_km': avoiding_distance - distance,
            'recommended': True
        }
    
    def _simulate_time_optimized_safe_route(self, origin_lat: float, origin_lng: float,
                                          dest_lat: float, dest_lng: float,
                                          hotspots: List[Dict]) -> Dict:
        """Simulate a time-optimized but still safe route."""
        distance = self._calculate_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Balance between time and safety
        optimized_distance = distance * 1.05  # Minimal detour
        optimized_time = optimized_distance * 1.1  # Faster route selection
        
        # Filter out only very high risk hotspots
        very_high_risk = [h for h in hotspots if h['risk_level'] == 'very_high']
        moderate_risk_hotspots = [h for h in hotspots if h['risk_level'] in ['medium', 'high']]
        
        safety_score = self._calculate_route_safety_score(
            origin_lat, origin_lng, dest_lat, dest_lng,
            {'distance_meters': optimized_distance * 1000, 'congestion_level': 'moderate'},
            moderate_risk_hotspots, 'optimized'
        )
        
        return {
            'route_type': 'time_optimized',
            'name': 'Time-Optimized Safe Route',
            'distance_km': optimized_distance,
            'duration_minutes': optimized_time,
            'safety_score': safety_score['overall_score'],
            'risk_factors': safety_score['risk_factors'],
            'congestion_level': 'moderate',
            'extra_distance_km': optimized_distance - distance,
            'recommended': safety_score['overall_score'] >= 0.6
        }
    
    def _calculate_route_safety_score(self, origin_lat: float, origin_lng: float,
                                    dest_lat: float, dest_lng: float,
                                    route_data: Dict, hotspots: List[Dict],
                                    route_type: str) -> Dict:
        """Calculate comprehensive safety score for a route."""
        base_score = 0.7  # Start with neutral score
        risk_factors = []
        
        # Factor 1: Congestion impact
        congestion_level = route_data.get('congestion_level', 'moderate')
        congestion_penalty = {
            'light': 0.1,
            'moderate': 0.0,
            'heavy': -0.15,
            'severe': -0.3
        }.get(congestion_level, 0.0)
        
        base_score += congestion_penalty
        if congestion_penalty < -0.1:
            risk_factors.append(f"High traffic congestion ({congestion_level})")
        
        # Factor 2: Hotspot proximity
        hotspot_penalty = 0
        for hotspot in hotspots:
            # Calculate distance from route to hotspot
            hotspot_distance = self._calculate_distance(
                (origin_lat + dest_lat) / 2,  # Route midpoint approximation
                (origin_lng + dest_lng) / 2,
                hotspot['latitude'],
                hotspot['longitude']
            )
            
            if hotspot_distance < 2.0:  # Within 2km of route
                penalty = self.risk_penalties.get(hotspot['risk_level'], 1.0) * 0.1
                hotspot_penalty += penalty
                risk_factors.append(f"Near {hotspot['name']} ({hotspot['risk_level']} risk)")
        
        base_score -= min(hotspot_penalty, 0.4)  # Cap penalty at 0.4
        
        # Factor 3: Route type bonus/penalty
        type_adjustments = {
            'direct': 0.0,
            'highway': 0.1,
            'avoiding': 0.2,
            'optimized': 0.05
        }
        base_score += type_adjustments.get(route_type, 0.0)
        
        # Factor 4: Time of day considerations
        current_hour = datetime.now().hour
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Rush hours
            base_score -= 0.1
            risk_factors.append("Rush hour traffic")
        elif 22 <= current_hour or current_hour <= 5:  # Late night
            base_score -= 0.05
            risk_factors.append("Low visibility (night time)")
        
        # Ensure score is within bounds
        final_score = max(0.0, min(1.0, base_score))
        
        return {
            'overall_score': round(final_score, 2),
            'risk_factors': risk_factors,
            'congestion_impact': congestion_penalty,
            'hotspot_impact': hotspot_penalty
        }
    
    def _select_safest_route(self, route_options: List[Dict], preferences: Dict) -> Dict:
        """Select the safest route based on preferences."""
        if not route_options:
            return self._get_fallback_route()
        
        # Filter by preferences
        max_extra_time = preferences.get('max_extra_time', 30)
        
        # Find the fastest route as baseline
        fastest_time = min(route['duration_minutes'] for route in route_options)
        
        # Filter routes that are within acceptable extra time
        acceptable_routes = [
            route for route in route_options
            if route['duration_minutes'] <= fastest_time + max_extra_time
        ]
        
        if not acceptable_routes:
            acceptable_routes = route_options
        
        # Select highest safety score among acceptable routes
        return max(acceptable_routes, key=lambda x: x['safety_score'])
    
    def _generate_route_recommendations(self, best_route: Dict, hotspots: List[Dict],
                                      preferences: Dict) -> List[str]:
        """Generate recommendations for the selected route."""
        recommendations = []
        
        # Safety recommendations
        if best_route['safety_score'] < 0.6:
            recommendations.append("⚠️ Consider alternate timing due to higher risk factors")
        
        if 'rush_hour' in str(best_route.get('risk_factors', [])):
            recommendations.append("🕐 Plan for extra travel time during rush hour")
        
        # Hotspot recommendations
        high_risk_nearby = [h for h in hotspots if h['risk_level'] in ['high', 'very_high']]
        if high_risk_nearby:
            recommendations.append(f"⚠️ {len(high_risk_nearby)} high-risk areas detected near route")
        
        # Weather recommendations
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 8:
            recommendations.append("🌅 Morning fog possible - reduce speed and increase following distance")
        elif 17 <= current_hour <= 19:
            recommendations.append("🌆 Peak traffic hours - expect delays and drive defensively")
        
        # Route-specific recommendations
        if best_route['route_type'] == 'highway':
            recommendations.append("🛣️ Highway route - maintain safe following distance at higher speeds")
        elif best_route['route_type'] == 'avoiding':
            recommendations.append("🔄 Route avoids known hotspots but may take longer")
        
        return recommendations
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in kilometers."""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng/2) * math.sin(dlng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _calculate_search_radius(self, origin_lat: float, origin_lng: float,
                               dest_lat: float, dest_lng: float) -> float:
        """Calculate appropriate search radius for hotspots."""
        route_distance = self._calculate_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Search radius should be proportional to route distance
        if route_distance < 5:
            return 3.0
        elif route_distance < 20:
            return 5.0
        elif route_distance < 50:
            return 10.0
        else:
            return 15.0
    
    def _get_fallback_route(self) -> Dict:
        """Get fallback route when no options are available."""
        return {
            'route_type': 'fallback',
            'name': 'Direct Route (Estimated)',
            'distance_km': 0,
            'duration_minutes': 0,
            'safety_score': 0.5,
            'risk_factors': ['No route data available'],
            'congestion_level': 'unknown',
            'recommended': False,
            'fallback': True
        }
    
    def get_hotspot_impact_analysis(self, route_data: Dict, hotspots: List[Dict]) -> Dict:
        """Analyze impact of hotspots on a specific route."""
        analysis = {
            'total_hotspots_nearby': len(hotspots),
            'high_risk_hotspots': 0,
            'medium_risk_hotspots': 0,
            'low_risk_hotspots': 0,
            'estimated_delay_minutes': 0,
            'safety_recommendations': []
        }
        
        for hotspot in hotspots:
            risk_level = hotspot['risk_level']
            
            if risk_level in ['high', 'very_high']:
                analysis['high_risk_hotspots'] += 1
                analysis['estimated_delay_minutes'] += 8
            elif risk_level == 'medium':
                analysis['medium_risk_hotspots'] += 1
                analysis['estimated_delay_minutes'] += 3
            else:
                analysis['low_risk_hotspots'] += 1
                analysis['estimated_delay_minutes'] += 1
        
        # Generate recommendations
        if analysis['high_risk_hotspots'] > 2:
            analysis['safety_recommendations'].append("Consider alternate route due to multiple high-risk areas")
        
        if analysis['estimated_delay_minutes'] > 15:
            analysis['safety_recommendations'].append(f"Allow extra {analysis['estimated_delay_minutes']} minutes for travel")
        
        return analysis