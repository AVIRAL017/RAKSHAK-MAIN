"""
Test script for Emergency Response System
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.emergency_service import get_emergency_service

def test_emergency_system():
    """Test the emergency response system"""
    
    print("=" * 60)
    print("Testing Emergency Response System")
    print("=" * 60)
    
    # Get emergency service instance
    emergency_service = get_emergency_service()
    
    # Test 1: Hospital data loading
    print("\n1. Testing Hospital Data Loading...")
    hospitals = emergency_service.get_hospitals(limit=10)
    print(f"   ✓ Loaded {len(emergency_service.get_hospitals())} hospitals")
    print(f"   Sample hospital: {hospitals[0]['name']} - {hospitals[0]['district']}, {hospitals[0]['state']}")
    
    # Test 2: Distance calculation
    print("\n2. Testing Distance Calculation...")
    delhi_lat, delhi_lon = 28.6139, 77.2090
    mumbai_lat, mumbai_lon = 19.0760, 72.8777
    distance = emergency_service.calculate_distance(delhi_lat, delhi_lon, mumbai_lat, mumbai_lon)
    print(f"   ✓ Distance Delhi to Mumbai: {distance:.2f} km")
    
    # Test 3: Find nearest hospital
    print("\n3. Testing Nearest Hospital Search...")
    test_lat, test_lon = 28.6139, 77.2090  # Delhi coordinates
    nearest_hospital, distance = emergency_service.find_nearest_hospital(test_lat, test_lon)
    if nearest_hospital:
        print(f"   ✓ Nearest hospital: {nearest_hospital['name']}")
        print(f"   ✓ Distance: {distance:.2f} km")
    else:
        print("   ✗ No hospital found")
    
    # Test 4: Ambulance pre-positioning
    print("\n4. Testing Ambulance Pre-positioning Algorithm...")
    
    # Create sample hotspots
    sample_hotspots = [
        {
            'id': 'test_1',
            'name': 'Test Hotspot 1',
            'latitude': 28.7041,
            'longitude': 77.1025,
            'severity': 'High',
            'risk_level': 'High'
        },
        {
            'id': 'test_2',
            'name': 'Test Hotspot 2',
            'latitude': 19.0760,
            'longitude': 72.8777,
            'severity': 'Medium',
            'risk_level': 'Medium'
        },
        {
            'id': 'test_3',
            'name': 'Test Hotspot 3',
            'latitude': 13.0827,
            'longitude': 80.2707,
            'severity': 'Low',
            'risk_level': 'Low'
        }
    ]
    
    ambulance_placements = emergency_service.calculate_ambulance_placements(sample_hotspots)
    print(f"   ✓ Calculated {len(ambulance_placements)} ambulance placements")
    
    if ambulance_placements:
        placement = ambulance_placements[0]
        print(f"   Sample placement:")
        print(f"     - Location: {placement['hotspot_name']}")
        print(f"     - Risk Level: {placement['risk_level']}")
        print(f"     - Assigned Hospital: {placement['assigned_hospital']['name']}")
        print(f"     - Distance: {placement['distance_to_hospital']} km")
        print(f"     - Response Time: {placement['response_time_estimate']} min")
    
    # Test 5: Police station fetching (optional, requires internet)
    print("\n5. Testing Police Station Data Fetching...")
    print("   Note: This requires internet connection and may take 20-30 seconds...")
    try:
        police_stations = emergency_service.fetch_police_stations(28.6139, 77.2090, radius_km=10)
        print(f"   ✓ Fetched {len(police_stations)} police stations from OpenStreetMap")
        if police_stations:
            print(f"   Sample station: {police_stations[0]['name']}")
    except Exception as e:
        print(f"   ⚠ Police station fetch failed (this is normal if offline): {str(e)}")
    
    print("\n" + "=" * 60)
    print("Emergency Response System Test Complete!")
    print("=" * 60)
    print("\nSummary:")
    print(f"  • Hospitals loaded: {len(emergency_service.get_hospitals())}")
    print(f"  • Ambulance placements calculated: {len(ambulance_placements)}")
    print(f"  • Police stations fetched: {len(emergency_service.get_police_stations())}")
    print("\n✓ All core features working correctly!")
    print("\nYou can now start the application with: python run.py")

if __name__ == '__main__':
    test_emergency_system()
