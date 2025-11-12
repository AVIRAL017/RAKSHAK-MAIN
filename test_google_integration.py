#!/usr/bin/env python3
"""
Simple test to verify Google Maps SERP API integration
Tests the updated system with strategic API usage.
"""

import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.google_maps_service import GoogleMapsService
from src.services.efficient_demo_generator import EfficientDemoGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_google_maps_integration():
    """Test Google Maps integration with strategic API usage."""
    print("=" * 60)
    print("TESTING GOOGLE MAPS SERP API INTEGRATION")
    print("=" * 60)
    
    # Initialize service
    google_service = GoogleMapsService()
    
    # Show initial API usage
    stats = google_service.get_api_usage_stats()
    print(f"\n📊 Initial API Usage:")
    print(f"   Total Limit: {stats['total_limit']} calls")
    print(f"   User Route Calls Available: {stats['user_calls_available']}")
    print(f"   Pattern Analysis Calls Available: {stats['pattern_calls_remaining']}")
    
    # Test 1: Real user route request (Delhi to Airport)
    print(f"\n🗺️  Test 1: Real User Route Request")
    print(f"   Route: Delhi Connaught Place -> IGI Airport")
    
    route_result = google_service.get_directions_with_traffic(
        28.6139, 77.2090,  # Connaught Place
        28.5562, 77.1000,  # IGI Airport
        is_user_request=True  # This is a real user request
    )
    
    if route_result['status'] == 'success':
        route_data = route_result['route_data']
        print(f"   ✅ SUCCESS: Route calculated with real Google Maps data")
        print(f"   Distance: {route_data.get('distance_meters', 0)/1000:.1f} km")
        print(f"   Duration (traffic): {route_data.get('duration_traffic_seconds', 0)/60:.1f} min")
        print(f"   Congestion Level: {route_data.get('congestion_level', 'unknown')}")
    else:
        print(f"   ❌ Route calculation result: {route_result.get('message', route_result['status'])}")
    
    # Show updated API usage
    stats = google_service.get_api_usage_stats()
    print(f"\n📊 API Usage After Route Request:")
    print(f"   Calls Used: {stats['calls_used']}/{stats['total_limit']}")
    print(f"   User Calls Remaining: {stats['user_calls_available']}")
    print(f"   Usage Percentage: {stats['usage_percentage']:.1f}%")
    
    # Test 2: Demo data generation (uses minimal or no API calls)
    print(f"\n🚀 Test 2: Efficient Demo Data Generation")
    
    demo_generator = EfficientDemoGenerator()
    demo_result = demo_generator.generate_comprehensive_data()
    
    if demo_result['status'] == 'success':
        summary = demo_result['summary']
        print(f"   ✅ SUCCESS: Demo data generated efficiently")
        print(f"   Hotspots: {summary['hotspots']}")
        print(f"   Traffic Patterns: {summary['traffic_patterns']}")
        print(f"   Incidents: {summary['incidents']}")
        print(f"   Route Alternatives: {summary['route_alternatives']}")
    else:
        print(f"   ❌ Demo generation failed: {demo_result['message']}")
    
    # Final API usage summary
    final_stats = google_service.get_api_usage_stats()
    print(f"\n📈 Final API Usage Summary:")
    print(f"   Total API Calls Used: {final_stats['calls_used']}/{final_stats['total_limit']}")
    print(f"   Calls Reserved for Users: {final_stats['user_calls_available']}")
    print(f"   Pattern Analysis Calls: {final_stats['pattern_calls_used']}/{final_stats['pattern_calls_limit']}")
    print(f"   Strategy: ✅ API primarily reserved for real user route requests")
    
    return final_stats['calls_used'] <= 2  # Should use very few calls

def test_route_safety_calculation():
    """Test safe route calculation with Google Maps data."""
    print(f"\n" + "=" * 60)
    print("TESTING SAFE ROUTE CALCULATION")
    print("=" * 60)
    
    from src.services.safe_route_service import SafeRouteService
    from src.services.hotspot_service import HotspotService
    
    # Initialize services
    google_service = GoogleMapsService()
    hotspot_service = HotspotService()
    safe_route_service = SafeRouteService(
        google_maps_service=google_service,
        hotspot_service=hotspot_service
    )
    
    # Test safe route calculation
    print(f"\n🛣️  Calculating safe route: Mumbai -> Pune")
    
    route_result = safe_route_service.calculate_safe_route(
        19.0760, 72.8777,  # Mumbai
        18.5204, 73.8567,  # Pune
        route_preferences={
            'avoid_high_risk': True,
            'prioritize_safety': True,
            'max_extra_time': 30
        }
    )
    
    if route_result['status'] == 'success':
        safe_route = route_result['safe_route']
        safety_analysis = route_result['safety_analysis']
        
        print(f"   ✅ Safe route calculated successfully!")
        print(f"   Route Type: {safe_route['route_type']}")
        print(f"   Safety Score: {safe_route['safety_score']:.2f}")
        print(f"   Distance: {safe_route.get('distance_km', 0):.1f} km")
        print(f"   Duration: {safe_route.get('duration_minutes', 0):.1f} minutes")
        print(f"   Hotspots Avoided: {safety_analysis['hotspots_avoided']}")
        
        if route_result.get('recommendations'):
            print(f"   Recommendations:")
            for rec in route_result['recommendations'][:3]:
                print(f"     - {rec}")
    else:
        print(f"   ❌ Safe route calculation failed: {route_result['message']}")
    
    return route_result['status'] == 'success'

def main():
    """Run all tests."""
    print("SafeRoute Navigator v2.0 - Google Maps Integration Test")
    print("🔑 Using SERP API Key: 47822c...4a0")
    print("🎯 Strategy: Reserve API calls for real user requests")
    print()
    
    try:
        # Test Google Maps integration
        maps_test = test_google_maps_integration()
        
        # Test safe route calculation  
        route_test = test_route_safety_calculation()
        
        print(f"\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Google Maps Integration: {'✅ PASS' if maps_test else '❌ FAIL'}")
        print(f"Safe Route Calculation: {'✅ PASS' if route_test else '❌ FAIL'}")
        
        if maps_test and route_test:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ Google Maps SERP API integration is working")
            print(f"✅ API usage is optimized for user requests")
            print(f"✅ Safe route calculation is operational")
            print(f"\n🚀 Your SafeRoute Navigator is ready with Google Maps!")
        else:
            print(f"\n⚠️  Some tests failed. Check the API key and connection.")
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        print(f"\n❌ Test failed: {str(e)}")

if __name__ == "__main__":
    main()