"""
Emergency Response Service
Handles hospitals, police stations, and ambulance pre-positioning logic
"""

import csv
import math
import os
import requests
from typing import List, Dict, Tuple, Optional
import logging
from src.services.police_data_fetcher import get_police_data_fetcher

logger = logging.getLogger(__name__)


class EmergencyService:
    """Service for managing emergency response infrastructure"""
    
    def __init__(self):
        self.hospitals = []
        self.police_stations = []
        self.ambulance_placements = []
        self.demo_ambulances = []  # Demo ambulances for development
        self._load_hospitals()
        self._load_police_stations_from_cache()  # Load from cache (fast)
        self._generate_demo_ambulances()
    
    def _load_hospitals(self):
        """Load hospital data from geocode_health_centre.csv"""
        try:
            csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'geocode_health_centre.csv')
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    try:
                        # Extract facility name and type
                        facility_type = row.get('Facility Type', '').strip().lower()
                        facility_name = row.get('Facility Name', '').strip()
                        
                        # Only include hospitals, district hospitals, and CHCs
                        if facility_type in ['dis_h', 'chc', 'phc']:
                            lat = float(row.get('Latitude', 0))
                            lon = float(row.get('Longitude', 0))
                            
                            # Validate coordinates and restrict to India bounds
                            in_bounds = (6.5 <= lat <= 35.5) and (68.0 <= lon <= 97.5)
                            if lat != 0 and lon != 0 and -90 <= lat <= 90 and -180 <= lon <= 180 and in_bounds:
                                hospital = {
                                    'name': facility_name,
                                    'type': facility_type,
                                    'latitude': lat,
                                    'longitude': lon,
                                    'district': row.get('District Name', 'Unknown'),
                                    'state': row.get('State Name', 'Unknown'),
                                    'address': row.get('Facility Address', 'N/A')
                                }
                                self.hospitals.append(hospital)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid hospital row: {e}")
                        continue
            
            logger.info(f"Loaded {len(self.hospitals)} hospitals")
            
        except FileNotFoundError:
            logger.error("Hospital data file not found")
            self.hospitals = []
        except Exception as e:
            logger.error(f"Error loading hospitals: {e}")
            self.hospitals = []
    
    def _load_police_stations_from_cache(self):
        """
        Load real police stations from cache (very fast - no API call)
        Cache is automatically refreshed every 24 hours in the background
        """
        try:
            fetcher = get_police_data_fetcher()
            
            # This will load from cache if valid (milliseconds)
            # or fetch from API if cache is stale (minutes, but happens in background)
            self.police_stations = fetcher.get_police_stations()
            
            logger.info(f"Loaded {len(self.police_stations)} real police stations from cache")
            
            # Log cache info
            cache_info = fetcher.get_cache_info()
            if cache_info.get('valid'):
                logger.info(f"Using cached data from {cache_info.get('fetched_at')} (age: {cache_info.get('age_hours', 0):.1f} hours)")
            else:
                logger.warning("Cache is stale or missing - data will be refreshed in background")
            
        except Exception as e:
            logger.error(f"Error loading police stations from cache: {e}")
            # Fall back to demo list
            self._generate_demo_police_stations()
    
    def _generate_demo_police_stations(self):
        """Generate demo police stations for major Indian cities."""
        # Demo police stations across major cities
        demo_stations = [
            # Delhi
            {'name': 'Connaught Place Police Station', 'latitude': 28.6304, 'longitude': 77.2177, 'city': 'Delhi', 'type': 'city'},
            {'name': 'Karol Bagh Police Station', 'latitude': 28.6519, 'longitude': 77.1900, 'city': 'Delhi', 'type': 'city'},
            {'name': 'Dwarka Police Station', 'latitude': 28.5921, 'longitude': 77.0460, 'city': 'Delhi', 'type': 'city'},
            {'name': 'Rohini Police Station', 'latitude': 28.7496, 'longitude': 77.0670, 'city': 'Delhi', 'type': 'city'},
            {'name': 'Saket Police Station', 'latitude': 28.5244, 'longitude': 77.2066, 'city': 'Delhi', 'type': 'city'},
            
            # Mumbai
            {'name': 'Colaba Police Station', 'latitude': 18.9067, 'longitude': 72.8147, 'city': 'Mumbai', 'type': 'city'},
            {'name': 'Bandra Police Station', 'latitude': 19.0596, 'longitude': 72.8295, 'city': 'Mumbai', 'type': 'city'},
            {'name': 'Andheri Police Station', 'latitude': 19.1136, 'longitude': 72.8697, 'city': 'Mumbai', 'type': 'city'},
            {'name': 'Dadar Police Station', 'latitude': 19.0176, 'longitude': 72.8481, 'city': 'Mumbai', 'type': 'city'},
            
            # Bangalore
            {'name': 'Koramangala Police Station', 'latitude': 12.9352, 'longitude': 77.6245, 'city': 'Bangalore', 'type': 'city'},
            {'name': 'Indiranagar Police Station', 'latitude': 12.9784, 'longitude': 77.6408, 'city': 'Bangalore', 'type': 'city'},
            {'name': 'Jayanagar Police Station', 'latitude': 12.9250, 'longitude': 77.5838, 'city': 'Bangalore', 'type': 'city'},
            {'name': 'Whitefield Police Station', 'latitude': 12.9698, 'longitude': 77.7499, 'city': 'Bangalore', 'type': 'city'},
            
            # Chennai
            {'name': 'T Nagar Police Station', 'latitude': 13.0418, 'longitude': 80.2341, 'city': 'Chennai', 'type': 'city'},
            {'name': 'Mylapore Police Station', 'latitude': 13.0339, 'longitude': 80.2619, 'city': 'Chennai', 'type': 'city'},
            {'name': 'Anna Nagar Police Station', 'latitude': 13.0878, 'longitude': 80.2088, 'city': 'Chennai', 'type': 'city'},
            
            # Hyderabad
            {'name': 'Banjara Hills Police Station', 'latitude': 17.4239, 'longitude': 78.4738, 'city': 'Hyderabad', 'type': 'city'},
            {'name': 'Jubilee Hills Police Station', 'latitude': 17.4399, 'longitude': 78.4080, 'city': 'Hyderabad', 'type': 'city'},
            {'name': 'Madhapur Police Station', 'latitude': 17.4485, 'longitude': 78.3908, 'city': 'Hyderabad', 'type': 'city'},
            
            # Kolkata
            {'name': 'Park Street Police Station', 'latitude': 22.5548, 'longitude': 88.3514, 'city': 'Kolkata', 'type': 'city'},
            {'name': 'Salt Lake Police Station', 'latitude': 22.5867, 'longitude': 88.4168, 'city': 'Kolkata', 'type': 'city'},
            
            # Pune
            {'name': 'Shivajinagar Police Station', 'latitude': 18.5304, 'longitude': 73.8567, 'city': 'Pune', 'type': 'city'},
            {'name': 'Kothrud Police Station', 'latitude': 18.5074, 'longitude': 73.8077, 'city': 'Pune', 'type': 'city'},
        ]
        
        self.police_stations = demo_stations
        logger.info(f"Generated {len(demo_stations)} demo police stations")
    
    def _generate_demo_ambulances(self):
        """Generate demo ambulances with realistic GPS locations for development."""
        # Create demo ambulances at strategic locations
        # These simulate real ambulances that would be tracked via GPS
        demo_ambulances = [
            # Delhi Area
            {'id': 'AMB-DL-001', 'latitude': 28.6289, 'longitude': 77.2065, 'status': 'available', 'city': 'Delhi', 'hospital': 'AIIMS Delhi'},
            {'id': 'AMB-DL-002', 'latitude': 28.6510, 'longitude': 77.2219, 'status': 'available', 'city': 'Delhi', 'hospital': 'LNJP Hospital'},
            {'id': 'AMB-DL-003', 'latitude': 28.5672, 'longitude': 77.2006, 'status': 'available', 'city': 'Delhi', 'hospital': 'Max Hospital'},
            {'id': 'AMB-DL-004', 'latitude': 28.6923, 'longitude': 77.1700, 'status': 'on-duty', 'city': 'Delhi', 'hospital': 'Fortis Hospital'},
            
            # Mumbai Area
            {'id': 'AMB-MH-001', 'latitude': 19.0176, 'longitude': 72.8561, 'status': 'available', 'city': 'Mumbai', 'hospital': 'KEM Hospital'},
            {'id': 'AMB-MH-002', 'latitude': 18.9894, 'longitude': 72.8360, 'status': 'available', 'city': 'Mumbai', 'hospital': 'Lilavati Hospital'},
            {'id': 'AMB-MH-003', 'latitude': 19.1076, 'longitude': 72.8263, 'status': 'on-duty', 'city': 'Mumbai', 'hospital': 'Hinduja Hospital'},
            
            # Bangalore Area
            {'id': 'AMB-KA-001', 'latitude': 12.9698, 'longitude': 77.5986, 'status': 'available', 'city': 'Bangalore', 'hospital': 'Victoria Hospital'},
            {'id': 'AMB-KA-002', 'latitude': 12.9352, 'longitude': 77.6245, 'status': 'available', 'city': 'Bangalore', 'hospital': 'Manipal Hospital'},
            {'id': 'AMB-KA-003', 'latitude': 13.0067, 'longitude': 77.5963, 'status': 'on-duty', 'city': 'Bangalore', 'hospital': 'St Johns Hospital'},
            
            # Chennai Area
            {'id': 'AMB-TN-001', 'latitude': 13.0827, 'longitude': 80.2707, 'status': 'available', 'city': 'Chennai', 'hospital': 'Apollo Hospital'},
            {'id': 'AMB-TN-002', 'latitude': 13.0569, 'longitude': 80.2570, 'status': 'available', 'city': 'Chennai', 'hospital': 'CMC Hospital'},
            
            # Hyderabad Area
            {'id': 'AMB-TS-001', 'latitude': 17.4065, 'longitude': 78.4772, 'status': 'available', 'city': 'Hyderabad', 'hospital': 'Care Hospital'},
            {'id': 'AMB-TS-002', 'latitude': 17.4485, 'longitude': 78.3908, 'status': 'available', 'city': 'Hyderabad', 'hospital': 'NIMS Hospital'},
        ]
        
        self.demo_ambulances = demo_ambulances
        logger.info(f"Generated {len(demo_ambulances)} demo ambulances for development")
    
    def fetch_police_stations(self, center_lat: float, center_lon: float, radius_km: float = 50) -> List[Dict]:
        """
        Fetch police station locations from OpenStreetMap Overpass API.
        Falls back to demo stations if API fails.
        
        Args:
            center_lat: Center latitude for search
            center_lon: Center longitude for search
            radius_km: Search radius in kilometers
        
        Returns:
            List of police station dictionaries
        """
        try:
            # Convert radius to meters for Overpass API
            radius_m = radius_km * 1000
            
            # Overpass API query for police stations
            overpass_url = "http://overpass-api.de/api/interpreter"
            
            # Query for amenity=police
            query = f"""
            [out:json][timeout:10];
            (
              node["amenity"="police"](around:{radius_m},{center_lat},{center_lon});
              way["amenity"="police"](around:{radius_m},{center_lat},{center_lon});
              relation["amenity"="police"](around:{radius_m},{center_lat},{center_lon});
            );
            out center;
            """
            
            response = requests.post(overpass_url, data={'data': query}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                police_stations = []
                
                for element in data.get('elements', []):
                    # Get coordinates
                    if element['type'] == 'node':
                        lat = element.get('lat')
                        lon = element.get('lon')
                    elif 'center' in element:
                        lat = element['center'].get('lat')
                        lon = element['center'].get('lon')
                    else:
                        continue
                    
                    # Get name and tags
                    tags = element.get('tags', {})
                    name = tags.get('name', 'Police Station')
                    
                    police_station = {
                        'id': element.get('id'),
                        'name': name,
                        'latitude': lat,
                        'longitude': lon,
                        'type': tags.get('police:type', 'police'),
                        'operator': tags.get('operator', 'Unknown')
                    }
                    
                    police_stations.append(police_station)
                
                if police_stations:
                    logger.info(f"Fetched {len(police_stations)} police stations from OpenStreetMap")
                    return police_stations
                else:
                    logger.warning("No police stations from API, using demo data")
                    return self._filter_police_by_location(center_lat, center_lon, radius_km)
            else:
                logger.error(f"Overpass API error: {response.status_code}, using demo data")
                return self._filter_police_by_location(center_lat, center_lon, radius_km)
                
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            logger.warning(f"API request failed: {e}, using demo data")
            return self._filter_police_by_location(center_lat, center_lon, radius_km)
        except Exception as e:
            logger.error(f"Error fetching police stations: {e}, using demo data")
            return self._filter_police_by_location(center_lat, center_lon, radius_km)
    
    def _filter_police_by_location(self, center_lat: float, center_lon: float, radius_km: float) -> List[Dict]:
        """Filter demo police stations by location."""
        filtered_stations = []
        for station in self.police_stations:
            distance = self.calculate_distance(
                center_lat, center_lon,
                station['latitude'], station['longitude']
            )
            if distance <= radius_km:
                station['distance_km'] = round(distance, 2)
                filtered_stations.append(station)
        return filtered_stations
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth using Haversine formula
        
        Args:
            lat1, lon1: Coordinates of first point
            lat2, lon2: Coordinates of second point
        
        Returns:
            Distance in kilometers
        """
        # Radius of Earth in kilometers
        R = 6371.0
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def find_nearest_hospital(self, latitude: float, longitude: float) -> Tuple[Optional[Dict], float]:
        """
        Find the nearest hospital to a given location
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        
        Returns:
            Tuple of (nearest hospital dict, distance in km)
        """
        if not self.hospitals:
            return None, float('inf')
        
        nearest_hospital = None
        min_distance = float('inf')
        
        for hospital in self.hospitals:
            distance = self.calculate_distance(
                latitude, longitude,
                hospital['latitude'], hospital['longitude']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_hospital = hospital
        
        return nearest_hospital, min_distance
    
    def get_demo_ambulances(self, center_lat: float = None, center_lon: float = None, radius_km: float = 50) -> List[Dict]:
        """
        Get demo ambulances for development/viewing phase.
        These simulate real GPS-tracked ambulances.
        In production, replace with real ambulance GPS data.
        
        Args:
            center_lat: Center latitude for filtering (optional)
            center_lon: Center longitude for filtering (optional)
            radius_km: Search radius in kilometers
        
        Returns:
            List of demo ambulance dictionaries with GPS locations
        """
        if center_lat is None or center_lon is None:
            # Return all demo ambulances
            return self.demo_ambulances
        
        # Filter by location
        filtered_ambulances = []
        for ambulance in self.demo_ambulances:
            distance = self.calculate_distance(
                center_lat, center_lon,
                ambulance['latitude'], ambulance['longitude']
            )
            if distance <= radius_km:
                ambulance_copy = ambulance.copy()
                ambulance_copy['distance_km'] = round(distance, 2)
                ambulance_copy['eta_minutes'] = round(distance / 40 * 60, 1)  # Assuming 40 km/h avg speed
                filtered_ambulances.append(ambulance_copy)
        
        return filtered_ambulances
    
    def calculate_ambulance_placements(self, hotspots: List[Dict], max_placements: int = 50, use_demo: bool = True) -> List[Dict]:
        """
        Calculate optimal ambulance placements at high-risk hotspots.
        In development mode, assigns demo ambulances to hotspots.
        
        Args:
            hotspots: List of accident hotspot dictionaries
            max_placements: Maximum number of ambulance placements to calculate (default: 50)
            use_demo: Use demo ambulances if True, otherwise calculate optimal placements
        
        Returns:
            List of ambulance placement dictionaries
        """
        if use_demo and self.demo_ambulances:
            # Use demo ambulances and assign them to nearest hotspots
            return self._assign_demo_ambulances_to_hotspots(hotspots, max_placements)
        
        # Original ambulance placement logic
        ambulance_placements = []
        
        # Filter for High and Medium risk hotspots
        high_medium_hotspots = [
            h for h in hotspots 
            if h.get('severity', '').lower() in ['high', 'medium', 'critical', 'very high']
            or h.get('risk_level', '').lower() in ['high', 'medium', 'very_high']
        ]
        
        # Limit to max_placements to avoid timeouts
        if len(high_medium_hotspots) > max_placements:
            # Prioritize Critical and High risk over Medium
            critical_high = [h for h in high_medium_hotspots if h.get('severity', '').lower() in ['critical', 'very high'] or h.get('risk_level', '').lower() in ['high', 'very_high']]
            medium = [h for h in high_medium_hotspots if h.get('severity', '').lower() == 'medium' or h.get('risk_level', '').lower() == 'medium']
            
            # Take all critical/high, then fill with medium up to max
            high_medium_hotspots = critical_high[:max_placements] + medium[:max(0, max_placements - len(critical_high))]
        
        logger.info(f"Processing {len(high_medium_hotspots)} high/medium risk hotspots (max: {max_placements})")
        
        for hotspot in high_medium_hotspots:
            try:
                hotspot_lat = hotspot.get('latitude', hotspot.get('lat'))
                hotspot_lon = hotspot.get('longitude', hotspot.get('lon'))
                
                if hotspot_lat is None or hotspot_lon is None:
                    continue
                
                # Find nearest hospital
                nearest_hospital, distance = self.find_nearest_hospital(hotspot_lat, hotspot_lon)
                
                if nearest_hospital:
                    placement = {
                        'id': f"ambulance_{hotspot.get('id', len(ambulance_placements))}",
                        'hotspot_name': hotspot.get('name', 'Unknown Location'),
                        'hotspot_id': hotspot.get('id'),
                        'latitude': hotspot_lat,
                        'longitude': hotspot_lon,
                        'risk_level': hotspot.get('severity', hotspot.get('risk_level', 'Unknown')),
                        'assigned_hospital': {
                            'name': nearest_hospital['name'],
                            'latitude': nearest_hospital['latitude'],
                            'longitude': nearest_hospital['longitude'],
                            'district': nearest_hospital['district']
                        },
                        'distance_to_hospital': round(distance, 2),
                        'response_time_estimate': round(distance / 40 * 60, 1)  # Assuming 40 km/h avg speed, in minutes
                    }
                    
                    ambulance_placements.append(placement)
                    
            except Exception as e:
                logger.warning(f"Error processing hotspot: {e}")
                continue
        
        self.ambulance_placements = ambulance_placements
        logger.info(f"Calculated {len(ambulance_placements)} ambulance placements")
        
        return ambulance_placements
    
    def _assign_demo_ambulances_to_hotspots(self, hotspots: List[Dict], max_placements: int) -> List[Dict]:
        """
        Assign demo ambulances to high-risk hotspots with nearest hospital.
        This simulates the real system where ambulances would be dispatched to hotspots.
        """
        placements = []
        
        # Filter for high-risk hotspots
        high_risk_hotspots = [
            h for h in hotspots 
            if h.get('severity', '').lower() in ['high', 'critical', 'very high']
            or h.get('risk_level', '').lower() in ['high', 'very_high']
        ][:max_placements]
        
        # Assign demo ambulances to hotspots
        for i, hotspot in enumerate(high_risk_hotspots):
            if i >= len(self.demo_ambulances):
                break
            
            ambulance = self.demo_ambulances[i]
            hotspot_lat = hotspot.get('latitude', hotspot.get('lat'))
            hotspot_lon = hotspot.get('longitude', hotspot.get('lon'))
            
            if hotspot_lat is None or hotspot_lon is None:
                continue
            
            # Find nearest hospital to hotspot
            nearest_hospital, hospital_distance = self.find_nearest_hospital(hotspot_lat, hotspot_lon)
            
            if nearest_hospital:
                # Calculate ambulance distance to hotspot
                ambulance_distance = self.calculate_distance(
                    ambulance['latitude'], ambulance['longitude'],
                    hotspot_lat, hotspot_lon
                )
                
                placement = {
                    'id': ambulance['id'],
                    'ambulance_status': ambulance['status'],
                    'current_hospital': ambulance['hospital'],
                    'hotspot_name': hotspot.get('name', 'Unknown Location'),
                    'hotspot_id': hotspot.get('id'),
                    'latitude': hotspot_lat,  # Ambulance positioned at hotspot
                    'longitude': hotspot_lon,
                    'risk_level': hotspot.get('severity', hotspot.get('risk_level', 'High')),
                    'assigned_hospital': {
                        'name': nearest_hospital['name'],
                        'latitude': nearest_hospital['latitude'],
                        'longitude': nearest_hospital['longitude'],
                        'district': nearest_hospital['district']
                    },
                    'distance_to_hospital': round(hospital_distance, 2),
                    'response_time_estimate': round(ambulance_distance / 40 * 60, 1)
                }
                
                placements.append(placement)
        
        logger.info(f"Assigned {len(placements)} demo ambulances to high-risk hotspots")
        return placements
    
    def get_hospitals(self, limit: Optional[int] = None) -> List[Dict]:
        """Get list of hospitals"""
        if limit:
            return self.hospitals[:limit]
        return self.hospitals
    
    def get_police_stations(self) -> List[Dict]:
        """Get list of police stations"""
        return self.police_stations
    
    def get_ambulance_placements(self) -> List[Dict]:
        """Get list of ambulance placements"""
        return self.ambulance_placements


# Global instance
_emergency_service = None


def get_emergency_service() -> EmergencyService:
    """Get or create global emergency service instance"""
    global _emergency_service
    if _emergency_service is None:
        _emergency_service = EmergencyService()
    return _emergency_service
