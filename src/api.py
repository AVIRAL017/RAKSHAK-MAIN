"""
RAKSHAK - API Blueprint
Comprehensive API endpoints for all services.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Import services
from src.services.route_service import route_service
from src.services.hotspot_service import hotspot_service
from src.services.weather_service import weather_service
from src.services.stats_service import StatsService
from src.auth.auth_service import auth_service
from src.services.google_maps_service import GoogleMapsService
# Removed: SafeRoute predictor service
from src.services.traffic_pattern_generator import TrafficPatternGenerator
from src.services.efficient_demo_generator import EfficientDemoGenerator
from src.services.user_activity_service import user_activity_service
from src.services.emergency_service import get_emergency_service
from src.services.incident_service import incident_service

# Database routes are now registered separately in app.py

# Initialize statistics service
stats_service = StatsService()

# Initialize Google Maps integration services
google_maps_service = GoogleMapsService()
traffic_generator = TrafficPatternGenerator()
efficient_demo_generator = EfficientDemoGenerator()
# Removed: SafeRoute predictor service initialization

# Generate initial demo data efficiently
try:
    demo_result = efficient_demo_generator.generate_comprehensive_data()
    if demo_result['status'] == 'success':
        print("✅ Initial demo data generated successfully")
        # Update hotspot service with the generated data
        if hasattr(hotspot_service, 'update_with_demo_data'):
            hotspot_service.update_with_demo_data(demo_result['data'])
except Exception as e:
    print(f"Could not generate initial demo data: {str(e)}")

logger = logging.getLogger(__name__)

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Error handler for API routes
@api_bp.errorhandler(Exception)
def handle_api_error(error):
    logger.error(f"API error: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.utcnow().isoformat()
    }), 500

# Health check endpoints
@api_bp.route('/health', methods=['GET'])
@api_bp.route('/status/health', methods=['GET'])
def health_check():
    """API health check."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'route_service': 'operational' if route_service.enabled else 'unavailable',
            'hotspot_service': 'operational' if hotspot_service.enabled else 'unavailable',
            'weather_service': 'operational' if weather_service.enabled else 'unavailable'
        }
    })

# Dashboard stats endpoint
@api_bp.route('/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get real dashboard statistics from dataset."""
    try:
        # Get real stats from CSV
        stats = stats_service.get_dashboard_stats()
        return jsonify({
            'status': 'success',
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load dashboard statistics'
        }), 500

# REMOVED: All route calculation, traffic analysis, and route alternatives endpoints - Feature removed from RAKSHAK

# Geocoding and location search endpoints
@api_bp.route('/geocoding/search', methods=['GET'])
def geocoding_search():
    """Search for locations using geocoding."""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Search query parameter (q) is required'
            }), 400
        
        limit = request.args.get('limit', type=int, default=10)
        proximity_lat = request.args.get('proximity', '').split(',')[0] if request.args.get('proximity') else None
        proximity_lng = request.args.get('proximity', '').split(',')[1] if request.args.get('proximity') and ',' in request.args.get('proximity') else None
        
        # Simple geocoding using our route service
        geocode_result = route_service.geocode(query)
        
        results = []
        if geocode_result['status'] == 'success':
            results.append({
                'name': query,
                'display_name': geocode_result['display_name'],
                'lat': geocode_result['latitude'],
                'lng': geocode_result['longitude'],
                'type': 'location',
                'relevance': 1.0
            })
        
        # Add some additional demo results for Indian cities
        demo_cities = [
            {'name': 'Delhi', 'lat': 28.6139, 'lng': 77.2090, 'display_name': 'New Delhi, India'},
            {'name': 'Mumbai', 'lat': 19.0760, 'lng': 72.8777, 'display_name': 'Mumbai, Maharashtra, India'},
            {'name': 'Bangalore', 'lat': 12.9716, 'lng': 77.5946, 'display_name': 'Bengaluru, Karnataka, India'},
            {'name': 'Chennai', 'lat': 13.0827, 'lng': 80.2707, 'display_name': 'Chennai, Tamil Nadu, India'},
            {'name': 'Kolkata', 'lat': 22.5726, 'lng': 88.3639, 'display_name': 'Kolkata, West Bengal, India'},
            {'name': 'Hyderabad', 'lat': 17.3850, 'lng': 78.4867, 'display_name': 'Hyderabad, Telangana, India'},
            {'name': 'Pune', 'lat': 18.5204, 'lng': 73.8567, 'display_name': 'Pune, Maharashtra, India'},
        ]
        
        # Add matching cities to results
        for city in demo_cities:
            if query.lower() in city['name'].lower() and len(results) < limit:
                results.append({
                    'name': city['name'],
                    'display_name': city['display_name'],
                    'lat': city['lat'],
                    'lng': city['lng'],
                    'type': 'city',
                    'relevance': 0.9 if query.lower() == city['name'].lower() else 0.7
                })
        
        return jsonify({
            'status': 'success',
            'data': {
                'query': query,
                'results': results[:limit],
                'count': len(results[:limit])
            }
        })
        
    except Exception as e:
        logger.error(f"Geocoding search error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Geocoding search failed: {str(e)}'
        }), 500

@api_bp.route('/geocoding/forward', methods=['GET'])
def forward_geocoding():
    """Forward geocoding - address to coordinates."""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Query parameter (q) is required'
            }), 400
        
        result = route_service.geocode(query)
        
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'data': {
                    'query': query,
                    'results': [{
                        'display_name': result['display_name'],
                        'latitude': result['latitude'],
                        'longitude': result['longitude'],
                        'lat': result['latitude'],  # Keep for backwards compatibility
                        'lng': result['longitude'], # Keep for backwards compatibility
                        'type': 'location'
                    }]
                }
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Forward geocoding error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Forward geocoding failed: {str(e)}'
        }), 500

@api_bp.route('/geocoding/reverse', methods=['GET'])
def reverse_geocoding():
    """Reverse geocoding - coordinates to display name (demo)."""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float) or request.args.get('lon', type=float)
        if lat is None or lng is None:
            return jsonify({'status': 'error', 'message': 'lat and lng are required'}), 400
        # Demo reverse: just echo a formatted name within India bounds
        in_bounds = 6.0 <= lat <= 38.0 and 68.0 <= lng <= 98.0
        display_name = f"{lat:.5f}, {lng:.5f} (India)" if in_bounds else f"{lat:.5f}, {lng:.5f}"
        return jsonify({
            'status': 'success',
            'data': [{
                'display_name': display_name,
                'latitude': lat,
                'longitude': lng,
                'lat': lat,
                'lng': lng,
                'type': 'location'
            }]
        })
    except Exception as e:
        logger.error(f"Reverse geocoding error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Reverse geocoding failed: {str(e)}'}), 500

# Hotspot-related endpoints
@api_bp.route('/hotspots', methods=['GET'])
def get_hotspots():
    """Get safety hotspots with filtering options."""
    try:
        # Get query parameters
        center_lat = request.args.get('lat', type=float)
        center_lng = request.args.get('lng', type=float) or request.args.get('lon', type=float)
        radius_km = request.args.get('radius', type=float, default=50)
        risk_filter = request.args.get('risk_filter')
        limit = request.args.get('limit', type=int, default=100)
        
        # Get hotspots
        result = hotspot_service.get_hotspots(
            center_lat=center_lat,
            center_lng=center_lng,
            radius_km=radius_km,
            risk_filter=risk_filter,
            limit=limit
        )
        
        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Hotspots retrieval error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve hotspots: {str(e)}'
        }), 500

@api_bp.route('/hotspots/personalized', methods=['GET'])
def get_personalized_hotspots():
    """Get personalized hotspots based on user location."""
    try:
        # Get required parameters
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float) or request.args.get('lon', type=float)
        radius_km = request.args.get('radius', type=float, default=25)
        
        if user_lat is None or user_lng is None:
            return jsonify({
                'status': 'error',
                'message': 'User location (lat, lng) is required for personalized hotspots'
            }), 400
        
        # Get user preferences from query params or request body
        user_preferences = {
            'risk_tolerance': request.args.get('risk_tolerance', 'medium'),
            'route_types': request.args.getlist('route_types') or ['balanced'],
            'avoid_types': request.args.getlist('avoid_types') or []
        }
        
        result = hotspot_service.get_personalized_hotspots(
            user_lat=user_lat,
            user_lng=user_lng,
            radius_km=radius_km,
            user_preferences=user_preferences
        )
        
        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Personalized hotspots error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get personalized hotspots: {str(e)}'
        }), 500

@api_bp.route('/hotspots/<hotspot_id>', methods=['GET'])
def get_hotspot_details(hotspot_id):
    """Get detailed information about a specific hotspot."""
    try:
        # For demo purposes, get all hotspots and find the requested one
        result = hotspot_service.get_hotspots(limit=1000)
        
        if result['status'] != 'success':
            return jsonify(result), 500
        
        # Find hotspot by ID
        hotspot = None
        for h in result['data']['hotspots']:
            if h['id'] == hotspot_id:
                hotspot = h
                break
        
        if not hotspot:
            return jsonify({
                'status': 'error',
                'message': f'Hotspot with ID {hotspot_id} not found'
            }), 404
        
        # Add additional details for single hotspot view
        hotspot['detailed_analysis'] = {
            'risk_assessment': f"This location shows {hotspot['risk_level']} risk conditions",
            'traffic_impact': f"Average delay of {hotspot['avg_delay_minutes']} minutes",
            'safety_recommendations': hotspot.get('mitigation_suggestions', []),
            'incident_history': hotspot.get('recent_incidents', []),
            'best_times_to_avoid': ['07:00-10:00', '17:00-20:00'] if hotspot['time_dependent'] else []
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'hotspot': hotspot,
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Hotspot details error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get hotspot details: {str(e)}'
        }), 500

# Weather-related endpoints
@api_bp.route('/weather/current', methods=['GET'])
def get_current_weather():
    """Get current weather data for location."""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float) or request.args.get('lon', type=float)
        
        if lat is None or lng is None:
            return jsonify({
                'status': 'error',
                'message': 'Location coordinates (lat, lng) are required'
            }), 400
        
        result = weather_service.get_current_weather(lat, lng)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Current weather error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get current weather: {str(e)}'
        }), 500

@api_bp.route('/weather/forecast', methods=['GET'])
def get_weather_forecast():
    """Get weather forecast for location."""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float) or request.args.get('lon', type=float)
        days = request.args.get('days', type=int, default=5)
        
        if lat is None or lng is None:
            return jsonify({
                'status': 'error',
                'message': 'Location coordinates (lat, lng) are required'
            }), 400
        
        if days < 1 or days > 10:
            days = 5  # Default to 5 days
        
        result = weather_service.get_weather_forecast(lat, lng, days)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Weather forecast error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get weather forecast: {str(e)}'
        }), 500

@api_bp.route('/weather/alerts', methods=['GET'])
def get_weather_alerts():
    """Get weather alerts for location."""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float) or request.args.get('lon', type=float)
        
        if lat is None or lng is None:
            return jsonify({
                'status': 'error',
                'message': 'Location coordinates (lat, lng) are required'
            }), 400
        
        result = weather_service.get_weather_alerts(lat, lng)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Weather alerts error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get weather alerts: {str(e)}'
        }), 500

# Analytics and statistics endpoints
@api_bp.route('/analytics/route-stats', methods=['GET'])
def get_route_statistics():
    """Get route calculation statistics."""
    try:
        # Demo statistics
        stats = {
            'total_routes_calculated': 15420,
            'average_calculation_time_ms': 1.2,
            'cache_hit_rate': 0.68,
            'most_popular_cities': [
                {'city': 'Delhi', 'count': 3240},
                {'city': 'Mumbai', 'count': 2890},
                {'city': 'Bangalore', 'count': 2156},
                {'city': 'Chennai', 'count': 1987},
                {'city': 'Hyderabad', 'count': 1654}
            ],
            'route_type_distribution': {
                'balanced': 0.45,
                'fastest': 0.28,
                'safest': 0.15,
                'shortest': 0.08,
                'eco': 0.04
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Route statistics error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get route statistics: {str(e)}'
        }), 500

# Alias endpoints for frontend compatibility
@api_bp.route('/analytics/routes', methods=['GET'])
def analytics_routes_alias():
    return get_route_statistics()

@api_bp.route('/analytics/hotspots', methods=['GET'])
def analytics_hotspots_alias():
    return get_hotspot_statistics()

@api_bp.route('/analytics/hotspot-stats', methods=['GET'])
def get_hotspot_statistics():
    """Get hotspot statistics and trends."""
    try:
        # Demo statistics
        stats = {
            'total_active_hotspots': 1247,
            'hotspots_by_type': {
                'traffic_congestion': 456,
                'accident_prone': 298,
                'construction': 187,
                'flooding_risk': 134,
                'pedestrian_risk': 108,
                'weather_risk': 64
            },
            'hotspots_by_risk_level': {
                'critical': 89,
                'high': 245,
                'medium': 578,
                'low': 335
            },
            'top_risk_cities': [
                {'city': 'Mumbai', 'avg_risk_score': 0.74},
                {'city': 'Delhi', 'avg_risk_score': 0.68},
                {'city': 'Kolkata', 'avg_risk_score': 0.65},
                {'city': 'Chennai', 'avg_risk_score': 0.58},
                {'city': 'Bangalore', 'avg_risk_score': 0.52}
            ],
            'recent_trends': {
                'new_hotspots_24h': 23,
                'resolved_incidents_24h': 45,
                'avg_incident_duration_hours': 3.2
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Hotspot statistics error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get hotspot statistics: {str(e)}'
        }), 500

# Comprehensive Statistics Endpoints
@api_bp.route('/stats/system', methods=['GET'])
def get_system_statistics():
    """Get comprehensive system statistics for admin dashboard."""
    try:
        stats = stats_service.get_system_stats()
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        logger.error(f"System statistics error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get system statistics: {str(e)}'
        }), 500

@api_bp.route('/stats/user', methods=['GET'])
@api_bp.route('/stats/user/<user_id>', methods=['GET'])
def get_user_dashboard_statistics(user_id=None):
    """Get user-specific dashboard statistics with real activity data."""
    try:
        # Use default demo user if none specified
        if not user_id:
            user_id = "demo_user"
        
        # Get real user activity data
        activity_data = user_activity_service.get_user_profile_data(user_id)
        
        return jsonify({
            'status': 'success',
            'data': activity_data
        })
    except Exception as e:
        logger.error(f"User dashboard statistics error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get user dashboard statistics: {str(e)}'
        }), 500

@api_bp.route('/stats/analytics', methods=['GET'])
def get_analytics_data():
    """Get detailed analytics data for charts and graphs."""
    try:
        time_range = request.args.get('range', '7d')
        analytics = stats_service.get_analytics_data(time_range)
        return jsonify({
            'status': 'success',
            'data': analytics,
            'time_range': time_range
        })
    except Exception as e:
        logger.error(f"Analytics data error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get analytics data: {str(e)}'
        }), 500

@api_bp.route('/stats/overview', methods=['GET'])
def get_stats_overview():
    """Get quick overview statistics for dashboards."""
    try:
        system_stats = stats_service.get_system_stats()
        overview = {
            'overview': system_stats.get('overview', {}),
            'recent_activity': system_stats.get('recent_activity', [])[:3],
            'alerts': system_stats.get('alerts', [])[:2],
            'performance': {
                'api_response_time': system_stats.get('performance', {}).get('api_response_time', 'N/A'),
                'error_rate': system_stats.get('performance', {}).get('error_rate', 'N/A'),
                'concurrent_users': system_stats.get('performance', {}).get('concurrent_users', 0)
            }
        }
        return jsonify({
            'status': 'success',
            'data': overview
        })
    except Exception as e:
        logger.error(f"Stats overview error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get stats overview: {str(e)}'
        }), 500

# Utility endpoints
@api_bp.route('/search', methods=['GET'])
def search_locations():
    """Search for locations and places."""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Search query parameter (q) is required'
            }), 400
        
        limit = request.args.get('limit', type=int, default=10)
        
        # Demo search results based on query
        demo_results = []
        major_cities = [
            'Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata',
            'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow'
        ]
        
        # Simple search matching
        for city in major_cities:
            if query.lower() in city.lower():
                geocode_result = route_service.geocode(city)
                if geocode_result['status'] == 'success':
                    demo_results.append({
                        'name': city,
                        'display_name': geocode_result['display_name'],
                        'type': 'city',
                        'coordinates': [geocode_result['latitude'], geocode_result['longitude']],
                        'country': 'India',
                        'relevance_score': 0.9 if query.lower() == city.lower() else 0.7
                    })
        
        # Limit results
        demo_results = demo_results[:limit]
        
        return jsonify({
            'status': 'success',
            'data': {
                'query': query,
                'results': demo_results,
                'count': len(demo_results),
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Location search error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Location search failed: {str(e)}'
        }), 500

# Routes endpoints (frontend compatibility)
@api_bp.route('/routes/calculate', methods=['GET'])
def calculate_route_endpoint():
    try:
        from_lat = request.args.get('from_lat', type=float)
        from_lng = request.args.get('from_lng', type=float)
        to_lat = request.args.get('to_lat', type=float)
        to_lng = request.args.get('to_lng', type=float)
        route_type = request.args.get('route_type', default='balanced')
        
        if None in (from_lat, from_lng, to_lat, to_lng):
            return jsonify({'status': 'error', 'message': 'from_lat, from_lng, to_lat, to_lng are required'}), 400
        
        # Use internal route calculation to produce geometry and stats
        data = route_service._calculate_route_data(from_lat, from_lng, to_lat, to_lng, route_type)
        
        response_data = {
            'distance_km': data['distance_km'],
            'duration_minutes': data['duration_minutes'],
            'traffic_delay_minutes': data['traffic_delay_minutes'],
            'safety_score': max(0.0, round(1.0 - data['risk_score'], 2)),
            'risk_score': data['risk_score'],
            'risk_level': data['risk_level'],
            'geometry': {
                'type': 'LineString',
                'coordinates': data['coordinates']
            },
            'waypoints': data['waypoints']
        }
        return jsonify({'status': 'success', 'data': response_data})
    except Exception as e:
        logger.error(f"Route calculate error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Route calculation failed: {str(e)}'}), 500

@api_bp.route('/routes/alternatives', methods=['GET'])
def route_alternatives_endpoint():
    try:
        from_lat = request.args.get('from_lat', type=float)
        from_lng = request.args.get('from_lng', type=float)
        to_lat = request.args.get('to_lat', type=float)
        to_lng = request.args.get('to_lng', type=float)
        if None in (from_lat, from_lng, to_lat, to_lng):
            return jsonify({'status': 'error', 'message': 'from_lat, from_lng, to_lat, to_lng are required'}), 400
        
        # Generate two slight variants
        variants = []
        for route_type in ['balanced', 'safest']:
            d = route_service._calculate_route_data(from_lat + 0.01, from_lng, to_lat - 0.01, to_lng, route_type)
            variants.append({
                'distance_km': d['distance_km'],
                'duration_minutes': d['duration_minutes'],
                'safety_score': max(0.0, round(1.0 - d['risk_score'], 2)),
                'risk_level': d['risk_level'],
                'geometry': { 'type': 'LineString', 'coordinates': d['coordinates'] }
            })
        return jsonify({'status': 'success', 'data': {'alternatives': variants}})
    except Exception as e:
        logger.error(f"Route alternatives error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to get route alternatives: {str(e)}'}), 500

# Service status endpoint
@api_bp.route('/status', methods=['GET'])
def get_service_status():
    """Get comprehensive service status."""
    try:
        return jsonify({
            'status': 'operational',
            'version': '2.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'route_service': {
                    'status': 'operational' if route_service.enabled else 'unavailable',
                    'features': ['geocoding', 'route_calculation', 'traffic_simulation', 'caching'],
                    'cache_size': len(getattr(route_service, 'cache', {}))
                },
                'hotspot_service': {
                    'status': 'operational' if hotspot_service.enabled else 'unavailable',
                    'features': ['safety_hotspots', 'personalization', 'risk_assessment'],
                    'base_hotspots': len(hotspot_service.base_hotspots)
                },
                'weather_service': {
                    'status': 'operational' if weather_service.enabled else 'unavailable',
                    'features': ['current_weather', 'forecasting', 'alerts', 'driving_impact'],
                    'supported_regions': list(weather_service.regional_climate.keys())
                }
            },
            'system_info': {
                'demo_mode': True,
                'external_dependencies': 'none',
                'data_source': 'local_demo_data',
                'uptime_info': 'Service started successfully'
            }
        })
        
    except Exception as e:
        logger.error(f"Service status error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get service status: {str(e)}'
        }), 500

# Authentication endpoints
@api_bp.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Login data required'
            }), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
        
        success, message, user = auth_service.login(email, password)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'user': user.to_dict() if user else None,
                'redirect_url': '/dashboard' if user and user.role == 'user' else '/admin'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 401
            
    except Exception as e:
        logger.error(f"Login endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Login failed'
        }), 500

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Registration data required'
            }), 400
        
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        if not all([email, username, password, full_name]):
            return jsonify({
                'status': 'error',
                'message': 'All fields are required'
            }), 400
        
        success, message, user = auth_service.register(email, username, password, full_name)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'user': user.to_dict() if user else None
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Registration endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Registration failed'
        }), 500

@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        auth_service.logout()
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Logout failed'
        }), 500

@api_bp.route('/auth/user', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    try:
        user = auth_service.get_current_user()
        if user:
            return jsonify({
                'status': 'success',
                'user': user.to_dict()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Not authenticated'
            }), 401
            
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get user info'
        }), 500

@api_bp.route('/auth/stats', methods=['GET'])
def get_auth_stats():
    """Get user statistics (admin only)"""
    try:
        user = auth_service.get_current_user()
        if not user or user.role != 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        stats = auth_service.get_user_stats()
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Auth stats error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get user statistics'
        }), 500

# Emergency Response Endpoints
@api_bp.route('/emergency/hospitals', methods=['GET'])
def get_hospitals():
    """Get hospital locations."""
    try:
        emergency_service = get_emergency_service()
        limit = request.args.get('limit', type=int)
        
        hospitals = emergency_service.get_hospitals(limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': {
                'hospitals': hospitals,
                'count': len(hospitals),
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Hospitals retrieval error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve hospitals: {str(e)}'
        }), 500

@api_bp.route('/emergency/police-stations', methods=['GET'])
def get_police_stations_endpoint():
    """Get police station locations from cache (fast)."""
    try:
        from src.services.police_data_fetcher import get_police_data_fetcher
        emergency_service = get_emergency_service()
        fetcher = get_police_data_fetcher()
        
        # Get parameters
        center_lat = request.args.get('lat', type=float)
        center_lon = request.args.get('lon', type=float) or request.args.get('lng', type=float)
        radius = request.args.get('radius', type=float, default=5000)  # Default: all India (large radius)
        limit = request.args.get('limit', type=int, default=1000)  # Limit for performance
        
        # Get all police stations from cache (FAST - no API call)
        all_stations = emergency_service.get_police_stations()
        
        # Filter by location if provided
        if center_lat and center_lon and radius < 5000:
            filtered_stations = []
            for station in all_stations:
                distance = emergency_service.calculate_distance(
                    center_lat, center_lon,
                    station['latitude'], station['longitude']
                )
                if distance <= radius:
                    station_copy = station.copy()
                    station_copy['distance_km'] = round(distance, 2)
                    filtered_stations.append(station_copy)
            police_stations = filtered_stations[:limit]
        else:
            # Return all stations (or limited number)
            police_stations = all_stations[:limit]
        
        # Get cache info
        cache_info = fetcher.get_cache_info()
        
        return jsonify({
            'status': 'success',
            'data': {
                'police_stations': police_stations,
                'count': len(police_stations),
                'total_available': len(all_stations),
                'source': 'openstreetmap_cached',
                'cache_info': {
                    'age_hours': cache_info.get('age_hours', 0),
                    'fetched_at': cache_info.get('fetched_at'),
                    'valid': cache_info.get('valid', False)
                },
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Police stations retrieval error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve police stations: {str(e)}'
        }), 500

@api_bp.route('/emergency/police-stations/cache-info', methods=['GET'])
def get_police_cache_info():
    """Get information about police stations cache."""
    try:
        from src.services.police_data_fetcher import get_police_data_fetcher
        fetcher = get_police_data_fetcher()
        cache_info = fetcher.get_cache_info()
        
        return jsonify({
            'status': 'success',
            'data': cache_info
        })
    except Exception as e:
        logger.error(f"Cache info error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get cache info: {str(e)}'
        }), 500

@api_bp.route('/emergency/police-stations/refresh', methods=['POST'])
def refresh_police_cache():
    """Force refresh police stations cache (admin only - takes several minutes)."""
    try:
        from src.services.police_data_fetcher import get_police_data_fetcher
        fetcher = get_police_data_fetcher()
        
        logger.warning("Force refresh requested - this will take several minutes...")
        
        # Force refresh from API
        stations = fetcher.get_police_stations(force_refresh=True)
        
        return jsonify({
            'status': 'success',
            'message': 'Police stations cache refreshed successfully',
            'data': {
                'count': len(stations),
                'refreshed_at': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Cache refresh error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to refresh cache: {str(e)}'
        }), 500

@api_bp.route('/emergency/ambulances', methods=['GET'])
def get_ambulances():
    """Get pre-positioned ambulance locations (demo ambulances for development)."""
    try:
        emergency_service = get_emergency_service()
        
        # Check mode: 'demo' for development, 'calculate' for production
        mode = request.args.get('mode', 'demo')  # Default to demo mode
        recalculate = request.args.get('recalculate', 'false').lower() == 'true'
        max_placements = request.args.get('max_placements', type=int, default=30)
        
        if mode == 'demo':
            # Use demo ambulances - simulate real GPS tracked ambulances
            center_lat = request.args.get('lat', type=float)
            center_lon = request.args.get('lon', type=float)
            radius = request.args.get('radius', type=float, default=50)
            
            # Get demo ambulances filtered by location
            ambulance_placements = emergency_service.get_demo_ambulances(center_lat, center_lon, radius)
            
            logger.info(f"Returning {len(ambulance_placements)} demo ambulances (Development Mode)")
        else:
            # Calculate ambulance placements based on hotspots
            if recalculate or not emergency_service.get_ambulance_placements():
                # Get current hotspots (limit to reduce processing time)
                hotspots_result = hotspot_service.get_hotspots(limit=200)
                
                if hotspots_result['status'] == 'success':
                    hotspots = hotspots_result['data']['hotspots']
                    # Use demo=True to assign demo ambulances to hotspots
                    ambulance_placements = emergency_service.calculate_ambulance_placements(
                        hotspots, 
                        max_placements=max_placements,
                        use_demo=True  # Use demo ambulances in development
                    )
                else:
                    ambulance_placements = []
            else:
                ambulance_placements = emergency_service.get_ambulance_placements()
        
        return jsonify({
            'status': 'success',
            'data': {
                'ambulances': ambulance_placements,
                'count': len(ambulance_placements),
                'mode': mode,
                'note': 'Using demo ambulances for development. Replace with real GPS data in production.',
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Ambulances retrieval error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve ambulances: {str(e)}'
        }), 500

@api_bp.route('/emergency/initialize', methods=['POST'])
def initialize_emergency_data():
    """Initialize all emergency response data."""
    try:
        emergency_service = get_emergency_service()
        
        # Get parameters
        data = request.get_json() or {}
        center_lat = data.get('lat', 28.6139)  # Default to Delhi
        center_lon = data.get('lon', 77.2090)
        radius = data.get('radius', 50)
        
        # Fetch police stations
        police_stations = emergency_service.fetch_police_stations(center_lat, center_lon, radius)
        
        # Calculate ambulance placements (limit to 30 for faster response)
        hotspots_result = hotspot_service.get_hotspots(limit=200)
        ambulance_placements = []
        
        if hotspots_result['status'] == 'success':
            hotspots = hotspots_result['data']['hotspots']
            ambulance_placements = emergency_service.calculate_ambulance_placements(hotspots, max_placements=30)
        
        return jsonify({
            'status': 'success',
            'message': 'Emergency response system initialized',
            'data': {
                'hospitals_count': len(emergency_service.get_hospitals()),
                'police_stations_count': len(police_stations),
                'ambulances_count': len(ambulance_placements),
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Emergency initialization error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to initialize emergency system: {str(e)}'
        }), 500

# Incident Reporting Endpoints
@api_bp.route('/incidents/report', methods=['POST'])
def report_incident():
    """Report a new safety incident (by user or admin)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Incident data required'
            }), 400
        
        # Use CSV-based incident service
        result = incident_service.report_incident(data)
        
        if result['status'] == 'success':
            # Update hotspot service with new incident (optional)
            try:
                hotspot_service.add_incident_report({
                    'id': result['data']['incident_id'],
                    'latitude': result['data']['latitude'],
                    'longitude': result['data']['longitude'],
                    'type': result['data']['incident_type'],
                    'severity': result['data']['severity'],
                    'timestamp': result['data']['created_at']
                })
            except Exception as e:
                logger.warning(f"Failed to update hotspot service: {e}")
            
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Incident reporting error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to report incident: {str(e)}'
        }), 500

@api_bp.route('/incidents', methods=['GET'])
def get_incidents():
    """Get reported incidents with filtering options."""
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        severity_filter = request.args.get('severity')
        limit = request.args.get('limit', type=int, default=100)
        
        # Build filters
        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if severity_filter:
            filters['severity'] = severity_filter
        if limit:
            filters['limit'] = limit
        
        # Use CSV-based incident service
        result = incident_service.get_incidents(filters)
        
        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Get incidents error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve incidents: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Get incidents error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve incidents: {str(e)}'
        }), 500
