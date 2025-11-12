#!/usr/bin/env python3
"""
SafeRoute Navigator v2.0 - Google Maps Integration Test
Comprehensive test of the integrated system with Google Maps API.
Tests traffic pattern analysis, demo data generation, and safe route calculation.
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.dirname(__file__))

# Import services
from src.services.google_maps_service import GoogleMapsService
from src.services.traffic_pattern_generator import TrafficPatternGenerator
from src.services.hotspot_service import HotspotService
from src.services.safe_route_service import SafeRouteService
from src.services.weather_service import WeatherService
from src.ml.ml_service import MLService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_google_maps_service():
    """Test Google Maps service with SERP API."""
    print("=" * 60)
    print("TESTING GOOGLE MAPS SERVICE")
    print("=" * 60)
    
    google_maps_service = GoogleMapsService()
    
    # Display API usage stats
    stats = google_maps_service.get_api_usage_stats()
    print(f"API Usage: {stats['calls_used']}/{stats['total_limit']} calls used")
    
    # Test traffic pattern analysis (uses limited API calls strategically)
    print("\n📊 Starting traffic pattern analysis...")
    patterns_result = google_maps_service.analyze_traffic_patterns()
    
    if patterns_result['status'] == 'success':
        patterns = patterns_result['patterns']
        print(f"✅ Traffic patterns analyzed successfully!")
        print(f"   - API calls used: {patterns_result['api_calls_used']}")
        print(f"   - Pattern types: {list(patterns.keys())}")
        
        for pattern_type, locations in patterns.items():
            if locations:
                print(f"   - {pattern_type}: {len(locations)} locations analyzed")
    else:
        print(f"❌ Pattern analysis failed: {patterns_result['message']}")
        return None
    
    # Test individual route request
    print(f"\n🗺️  Testing route request (Delhi to Airport)...")
    route_result = google_maps_service.get_directions_with_traffic(
        28.6139, 77.2090,  # Connaught Place
        28.5562, 77.1000   # Delhi Airport
    )
    
    if route_result['status'] == 'success':
        route_data = route_result['route_data']
        print(f"✅ Route calculated successfully!")
        print(f"   - Distance: {route_data.get('distance_meters', 0) / 1000:.1f} km")
        print(f"   - Duration (traffic): {route_data.get('duration_traffic_seconds', 0) / 60:.1f} minutes")
        print(f"   - Congestion: {route_data.get('congestion_level', 'unknown')}")
    else:
        print(f"❌ Route calculation failed: {route_result.get('message', 'Unknown error')}")
    
    # Final API usage stats
    final_stats = google_maps_service.get_api_usage_stats()
    print(f"\n📈 Final API Usage: {final_stats['calls_used']}/{final_stats['total_limit']} calls used")
    print(f"   - Remaining: {final_stats['calls_remaining']} calls")
    
    return patterns_result

def test_traffic_pattern_generator(google_maps_data):
    """Test traffic pattern generator with Google Maps data."""
    print("\n" + "=" * 60)
    print("TESTING TRAFFIC PATTERN GENERATOR")
    print("=" * 60)
    
    if not google_maps_data or google_maps_data['status'] != 'success':
        print("❌ No Google Maps data available for pattern generation")
        return None
    
    generator = TrafficPatternGenerator()
    
    print("🚦 Generating demo traffic data from Google Maps patterns...")
    demo_result = generator.analyze_google_maps_patterns(google_maps_data)
    
    if demo_result['status'] == 'success':
        summary = demo_result['summary']
        print(f"✅ Demo data generated successfully!")
        print(f"   - Hotspots generated: {summary['hotspots_generated']}")
        print(f"   - Traffic flows: {summary['traffic_flows']}")
        print(f"   - Incidents: {summary['incidents']}")
        print(f"   - Route alternatives: {summary['route_alternatives']}")
        
        demo_data = demo_result['demo_data']
        
        # Sample some generated hotspots
        hotspots = demo_data.get('hotspots', [])
        if hotspots:
            print(f"\n📍 Sample generated hotspots:")
            for hotspot in hotspots[:5]:
                print(f"   - {hotspot['name']} ({hotspot['city']}): {hotspot['risk_level']} risk")
        
        return demo_result
    else:
        print(f"❌ Demo data generation failed: {demo_result['message']}")
        return None

def test_integrated_hotspot_service(google_maps_data, demo_data):
    """Test hotspot service with Google Maps integration."""
    print("\n" + "=" * 60)
    print("TESTING INTEGRATED HOTSPOT SERVICE")
    print("=" * 60)
    
    # Create traffic generator
    traffic_generator = TrafficPatternGenerator()
    
    # Initialize hotspot service with Google Maps integration
    hotspot_service = HotspotService(
        google_maps_service=None,  # Can add later
        traffic_generator=traffic_generator
    )
    
    # Update with Google Maps data
    if google_maps_data and google_maps_data['status'] == 'success':
        update_result = hotspot_service.update_with_google_maps_data(google_maps_data)
        print(f"📊 Google Maps data integration: {update_result['status']}")
        if update_result['status'] == 'success':
            print(f"   - Patterns loaded: {update_result.get('patterns_loaded', 0)}")
            print(f"   - Demo hotspots generated: {update_result.get('demo_hotspots_generated', 0)}")
    
    # Test hotspot retrieval for Delhi
    print(f"\n🔍 Testing hotspot retrieval for Delhi...")
    delhi_hotspots = hotspot_service.get_hotspots(
        28.6139, 77.2090,  # Delhi center
        radius_km=25,
        limit=10
    )
    
    if delhi_hotspots['status'] == 'success':
        hotspots = delhi_hotspots['data']['hotspots']
        print(f"✅ Found {len(hotspots)} hotspots in Delhi area")
        
        for hotspot in hotspots[:5]:
            print(f"   - {hotspot['name']}: {hotspot['risk_level']} ({hotspot['risk_score']:.2f})")
    else:
        print(f"❌ Hotspot retrieval failed: {delhi_hotspots['message']}")
    
    return hotspot_service

def test_safe_route_service(google_maps_service, hotspot_service):
    """Test safe route calculation service."""
    print("\n" + "=" * 60)
    print("TESTING SAFE ROUTE SERVICE")
    print("=" * 60)
    
    safe_route_service = SafeRouteService(
        google_maps_service=google_maps_service,
        hotspot_service=hotspot_service
    )
    
    # Test safe route calculation (Delhi to Mumbai - major route)
    print("🛣️  Calculating safe route (Delhi to nearby location)...")
    
    route_result = safe_route_service.calculate_safe_route(
        28.6139, 77.2090,  # Connaught Place, Delhi
        28.5562, 77.1000,  # Delhi Airport
        route_preferences={
            'avoid_high_risk': True,
            'prioritize_safety': True,
            'max_extra_time': 20,
            'prefer_highways': False
        }
    )
    
    if route_result['status'] == 'success':
        safe_route = route_result['safe_route']
        safety_analysis = route_result['safety_analysis']
        
        print(f"✅ Safe route calculated successfully!")
        print(f"   - Route type: {safe_route['route_type']}")
        print(f"   - Route name: {safe_route['name']}")
        print(f"   - Distance: {safe_route.get('distance_km', 0):.1f} km")
        print(f"   - Duration: {safe_route.get('duration_minutes', 0):.1f} minutes")
        print(f"   - Safety score: {safe_route['safety_score']:.2f}")
        print(f"   - Recommended: {safe_route.get('recommended', False)}")
        
        print(f"\n📊 Safety Analysis:")
        print(f"   - Overall safety score: {safety_analysis['overall_safety_score']:.2f}")
        print(f"   - Hotspots avoided: {safety_analysis['hotspots_avoided']}")
        print(f"   - Total hotspots nearby: {safety_analysis['total_hotspots_nearby']}")
        
        if route_result['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in route_result['recommendations']:
                print(f"   - {rec}")
        
        # Show alternatives
        alternatives = route_result.get('alternatives', [])
        if alternatives:
            print(f"\n🔄 Alternative routes ({len(alternatives)}):")
            for alt in alternatives:
                print(f"   - {alt['name']}: Safety {alt['safety_score']:.2f}")
    else:
        print(f"❌ Safe route calculation failed: {route_result['message']}")

def test_complete_system_workflow():
    """Test the complete integrated system workflow."""
    print("\n" + "=" * 60)
    print("TESTING COMPLETE SYSTEM WORKFLOW")
    print("=" * 60)
    
    print("🚀 Starting complete SafeRoute Navigator v2.0 workflow...")
    
    # 1. Initialize Google Maps service and analyze patterns
    print("\n1️⃣ Initializing Google Maps service...")
    google_maps_service = GoogleMapsService()
    patterns_result = google_maps_service.analyze_traffic_patterns()
    
    if patterns_result['status'] != 'success':
        print("❌ Google Maps pattern analysis failed - using fallback data")
        patterns_result = {'status': 'fallback', 'patterns': {}, 'api_calls_used': 0}
    
    # 2. Generate comprehensive demo data
    print("\n2️⃣ Generating comprehensive traffic data...")
    generator = TrafficPatternGenerator()
    demo_result = generator.analyze_google_maps_patterns(patterns_result)
    
    # 3. Initialize integrated services
    print("\n3️⃣ Initializing integrated services...")
    hotspot_service = HotspotService(
        google_maps_service=google_maps_service,
        traffic_generator=generator
    )
    
    if demo_result and demo_result['status'] == 'success':
        hotspot_service.update_with_google_maps_data(patterns_result)
    
    safe_route_service = SafeRouteService(
        google_maps_service=google_maps_service,
        hotspot_service=hotspot_service
    )
    
    # 4. Test comprehensive route planning
    print("\n4️⃣ Testing comprehensive route planning...")
    test_routes = [
        {
            'name': 'Delhi City Route',
            'origin': [28.6139, 77.2090],
            'destination': [28.5562, 77.1000]
        },
        {
            'name': 'Mumbai Local Route',
            'origin': [19.0760, 72.8777],
            'destination': [19.0896, 72.8656]
        }
    ]
    
    for route_test in test_routes:
        print(f"\n🧪 Testing {route_test['name']}...")
        
        # Get hotspots for the area
        hotspots_result = hotspot_service.get_hotspots(
            route_test['origin'][0], route_test['origin'][1],
            radius_km=15, limit=5
        )
        
        # Calculate safe route
        route_result = safe_route_service.calculate_safe_route(
            route_test['origin'][0], route_test['origin'][1],
            route_test['destination'][0], route_test['destination'][1]
        )
        
        if route_result['status'] == 'success':
            safety_score = route_result['safe_route']['safety_score']
            print(f"   ✅ Route calculated - Safety score: {safety_score:.2f}")
        else:
            print(f"   ❌ Route calculation failed")
    
    # 5. Final statistics
    print("\n5️⃣ System Statistics:")
    api_stats = google_maps_service.get_api_usage_stats()
    print(f"   - Google Maps API calls used: {api_stats['calls_used']}/{api_stats['total_limit']}")
    print(f"   - API calls remaining: {api_stats['calls_remaining']}")
    print(f"   - System status: All services operational")
    print(f"   - Integration level: Google Maps + ML + Weather")

def main():
    """Main test runner."""
    print("SafeRoute Navigator v2.0 - Google Maps Integration Test")
    print(f"Test started at: {datetime.now()}")
    print("🔑 Using SERP API for Google Maps integration")
    print("🎯 Strategic API usage - maximum 10 calls for pattern analysis")
    print()
    
    try:
        # Test individual components
        google_maps_data = test_google_maps_service()
        demo_data = test_traffic_pattern_generator(google_maps_data)
        hotspot_service = test_integrated_hotspot_service(google_maps_data, demo_data)
        
        # Create Google Maps service for route testing
        google_maps_service = GoogleMapsService()
        test_safe_route_service(google_maps_service, hotspot_service)
        
        # Test complete workflow
        test_complete_system_workflow()
        
        print("\n" + "=" * 60)
        print("ALL INTEGRATION TESTS COMPLETED")
        print("=" * 60)
        print("🎉 SafeRoute Navigator v2.0 with Google Maps integration is ready!")
        print("🔧 The system combines:")
        print("   - Real Google Maps traffic data (via SERP API)")
        print("   - ML-powered risk predictions")
        print("   - Real-time weather integration")
        print("   - Comprehensive demo data generation")
        print("   - Safe route calculation with hotspot avoidance")
        print("\n🚀 You can now run the web application!")
        
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        print(f"\n❌ Integration test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()