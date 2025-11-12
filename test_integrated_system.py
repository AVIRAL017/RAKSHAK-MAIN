#!/usr/bin/env python3
"""
Test script for integrated ML-powered SafeRoute Navigator v2.0 system.
Tests weather service, ML service, and hotspot service integration.
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.dirname(__file__))

# Import services
from src.services.weather_service import WeatherService
from src.ml.ml_service import MLService
from src.services.hotspot_service import HotspotService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_weather_service():
    """Test weather service with real API data."""
    print("=" * 60)
    print("TESTING WEATHER SERVICE")
    print("=" * 60)
    
    weather_service = WeatherService()
    
    # Test locations
    test_locations = [
        (28.6139, 77.2090, "New Delhi"),
        (19.0760, 72.8777, "Mumbai"),
        (12.9716, 77.5946, "Bangalore")
    ]
    
    for lat, lng, city in test_locations:
        print(f"\nTesting weather for {city} ({lat}, {lng}):")
        
        # Test current weather
        current = weather_service.get_current_weather(lat, lng)
        if current['status'] == 'success':
            data = current['data']
            print(f"  Current: {data['current']['description']}")
            print(f"  Temperature: {data['current']['temperature_c']}°C")
            print(f"  Humidity: {data['current']['humidity_percent']}%")
            print(f"  Risk Factor: {data['driving_conditions']['risk_factor']}")
        else:
            print(f"  Error: {current['message']}")
        
        # Test weather alerts
        alerts = weather_service.get_weather_alerts(lat, lng)
        if alerts['status'] == 'success' and alerts['data']:
            print(f"  Active Alerts: {len(alerts['data'])} alerts")
        else:
            print("  No active alerts")

def test_ml_service():
    """Test ML service for hotspot predictions."""
    print("\n" + "=" * 60)
    print("TESTING ML SERVICE")
    print("=" * 60)
    
    ml_service = MLService()
    
    # Test prediction with sample data
    test_data = {
        'weather': {
            'temperature': 25.0,
            'humidity': 65,
            'wind_speed': 10.0,
            'pressure': 1013.25,
            'visibility': 8000,
            'rain_1h': 0.0
        },
        'road_type': 'arterial',
        'traffic_density': 0.7,
        'location': {
            'latitude': 28.6139,
            'longitude': 77.2090
        }
    }
    
    print("\nTesting ML hotspot risk prediction:")
    prediction = ml_service.predict_hotspot_risk(test_data)
    
    if prediction['status'] == 'success':
        predictions = prediction['predictions']
        risk_data = predictions.get('risk', {})
        print(f"  Risk Level: {risk_data.get('risk_level', 'unknown')}")
        print(f"  Probability: {risk_data.get('probability', 0):.3f}")
        print(f"  Confidence: {risk_data.get('confidence', 0):.3f}")
        if 'category' in predictions:
            print(f"  Predicted Category: {predictions['category']}")
    else:
        print(f"  ML Prediction failed: {prediction['message']}")

def test_hotspot_service():
    """Test hotspot service with ML integration."""
    print("\n" + "=" * 60)
    print("TESTING HOTSPOT SERVICE (ML-INTEGRATED)")
    print("=" * 60)
    
    hotspot_service = HotspotService()
    
    # Test locations
    test_locations = [
        (28.6139, 77.2090, "New Delhi"),
        (19.0760, 72.8777, "Mumbai")
    ]
    
    for lat, lng, city in test_locations:
        print(f"\nTesting hotspots for {city}:")
        
        # Get hotspots
        hotspots = hotspot_service.get_hotspots(lat, lng, 10.0, limit=5)
        
        if hotspots['status'] == 'success':
            data = hotspots['data']
            print(f"  Found {len(data['hotspots'])} hotspots")
            for hotspot in data['hotspots'][:3]:  # Show first 3
                print(f"    - {hotspot['name']}: {hotspot['risk_level']} "
                      f"({hotspot['risk_score']:.2f}) - {hotspot['type']}")
                if hotspot.get('recent_incidents'):
                    print(f"      Recent incidents: {len(hotspot['recent_incidents'])}")
        else:
            print(f"  Error: {hotspots['message']}")
        
        # Test personalized hotspots
        user_preferences = {
            'priority_types': ['accident_prone', 'traffic_congestion'],
            'max_risk_tolerance': 0.7,
            'avoid_construction': True
        }
        
        personalized = hotspot_service.get_personalized_hotspots(
            lat, lng, 15.0, user_preferences
        )
        
        if personalized['status'] == 'success':
            print(f"  Personalized hotspots: {len(personalized['data']['hotspots'])}")
        else:
            print(f"  Personalized error: {personalized['message']}")

def test_system_integration():
    """Test overall system integration."""
    print("\n" + "=" * 60)
    print("TESTING SYSTEM INTEGRATION")
    print("=" * 60)
    
    # Test that services can work together
    weather_service = WeatherService()
    ml_service = MLService()
    hotspot_service = HotspotService()
    
    # Test location
    lat, lng = 28.6139, 77.2090  # New Delhi
    
    print(f"Integration test for coordinates ({lat}, {lng}):")
    
    # 1. Get weather data
    weather = weather_service.get_current_weather(lat, lng)
    weather_success = weather['status'] == 'success'
    print(f"  Weather Service: {'✓' if weather_success else '✗'}")
    
    # 2. Test ML prediction if weather is available
    if weather_success:
        location_data = {
            'weather': weather['data']['current'],
            'road_type': 'arterial',
            'traffic_density': 0.6,
            'location': {'latitude': lat, 'longitude': lng}
        }
        
        ml_prediction = ml_service.predict_hotspot_risk(location_data)
        ml_success = ml_prediction['status'] == 'success'
        print(f"  ML Service: {'✓' if ml_success else '✗'}")
    else:
        print("  ML Service: Skipped (no weather data)")
    
    # 3. Get hotspots (should work with or without ML)
    hotspots = hotspot_service.get_hotspots(lat, lng, 5.0, limit=3)
    hotspot_success = hotspots['status'] == 'success'
    print(f"  Hotspot Service: {'✓' if hotspot_success else '✗'}")
    
    # Summary
    total_tests = 3
    passed_tests = sum([weather_success, ml_success if weather_success else True, hotspot_success])
    print(f"\nIntegration Summary: {passed_tests}/{total_tests} services working")

if __name__ == "__main__":
    print("SafeRoute Navigator v2.0 - Integrated System Test")
    print(f"Test started at: {datetime.now()}")
    
    try:
        test_weather_service()
        test_ml_service() 
        test_hotspot_service()
        test_system_integration()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)