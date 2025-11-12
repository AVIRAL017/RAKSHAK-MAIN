"""
Police Stations Data Fetcher with Caching
Fetches all police stations in India from OpenStreetMap Overpass API
Implements intelligent caching to avoid slow API calls on every page load
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)

class PoliceDataFetcher:
    """Fetch and cache police station data from OpenStreetMap"""
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize the police data fetcher
        
        Args:
            cache_dir: Directory to store cache files (default: data/)
        """
        if cache_dir is None:
            # Default to data directory in project root
            self.cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data'
            )
        else:
            self.cache_dir = cache_dir
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.cache_file = os.path.join(self.cache_dir, 'police_stations.json')
        self.cache_validity_hours = 24  # Cache valid for 24 hours
        
        # Overpass API endpoint
        self.overpass_url = 'https://overpass-api.de/api/interpreter'
        
        # Overpass QL query for all police stations in India
        self.overpass_query = """
[out:json][timeout:300];
area["ISO3166-1"="IN"][admin_level=2]->.searchArea;
(
  node["amenity"="police"](area.searchArea);
  way["amenity"="police"](area.searchArea);
  relation["amenity"="police"](area.searchArea);
);
out center;
"""
    
    def is_cache_valid(self) -> bool:
        """
        Check if cache file exists and is still valid (less than 24 hours old)
        
        Returns:
            True if cache is valid, False otherwise
        """
        if not os.path.exists(self.cache_file):
            logger.info("Cache file does not exist")
            return False
        
        try:
            # Get file modification time
            file_mtime = os.path.getmtime(self.cache_file)
            file_age = datetime.now() - datetime.fromtimestamp(file_mtime)
            
            # Check if file is less than cache_validity_hours old
            is_valid = file_age < timedelta(hours=self.cache_validity_hours)
            
            if is_valid:
                logger.info(f"Cache is valid (age: {file_age.total_seconds() / 3600:.1f} hours)")
            else:
                logger.info(f"Cache is stale (age: {file_age.total_seconds() / 3600:.1f} hours)")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False
    
    def load_from_cache(self) -> Optional[List[Dict]]:
        """
        Load police stations data from cache file
        
        Returns:
            List of police station dictionaries, or None if loading fails
        """
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stations = data.get('stations', [])
            logger.info(f"Loaded {len(stations)} police stations from cache")
            return stations
            
        except Exception as e:
            logger.error(f"Error loading cache file: {e}")
            return None
    
    def save_to_cache(self, stations: List[Dict]) -> bool:
        """
        Save police stations data to cache file
        
        Args:
            stations: List of police station dictionaries
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            cache_data = {
                'fetched_at': datetime.now().isoformat(),
                'count': len(stations),
                'stations': stations
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(stations)} police stations to cache")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            return False
    
    def fetch_from_overpass(self) -> Optional[List[Dict]]:
        """
        Fetch all police stations in India from Overpass API
        This is a slow operation that can take several minutes
        
        Returns:
            List of police station dictionaries, or None if fetch fails
        """
        logger.info("Starting Overpass API query for all police stations in India...")
        logger.warning("This may take several minutes (up to 5 minutes). Please wait...")
        
        try:
            # Make POST request to Overpass API
            start_time = time.time()
            
            response = requests.post(
                self.overpass_url,
                data={'data': self.overpass_query},
                timeout=360  # 6 minute timeout
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Overpass API responded in {elapsed:.1f} seconds")
            
            if response.status_code != 200:
                logger.error(f"Overpass API error: HTTP {response.status_code}")
                return None
            
            # Parse JSON response
            data = response.json()
            elements = data.get('elements', [])
            
            logger.info(f"Received {len(elements)} elements from Overpass API")
            
            # Parse and clean the data
            stations = []
            
            for element in elements:
                try:
                    # Get coordinates based on element type
                    if element['type'] == 'node':
                        lat = element.get('lat')
                        lon = element.get('lon')
                    elif 'center' in element:
                        lat = element['center'].get('lat')
                        lon = element['center'].get('lon')
                    else:
                        continue
                    
                    # Validate coordinates
                    if lat is None or lon is None:
                        continue
                    
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        continue
                    
                    # Get tags
                    tags = element.get('tags', {})
                    name = tags.get('name', 'Police Station')
                    
                    # Create station dictionary
                    station = {
                        'id': f"osm-{element.get('id')}",
                        'name': name,
                        'latitude': lat,
                        'longitude': lon,
                        'type': tags.get('police:type', 'police'),
                        'operator': tags.get('operator', 'Unknown'),
                        'address': tags.get('addr:full') or tags.get('addr:street', ''),
                        'city': tags.get('addr:city', ''),
                        'state': tags.get('addr:state', ''),
                        'pincode': tags.get('addr:postcode', ''),
                        'phone': tags.get('phone', ''),
                        'source': 'openstreetmap'
                    }
                    
                    stations.append(station)
                    
                except Exception as e:
                    logger.warning(f"Error parsing element: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(stations)} valid police stations")
            return stations
            
        except requests.exceptions.Timeout:
            logger.error("Overpass API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error fetching from Overpass API: {e}")
            return None
    
    def get_police_stations(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get police stations data - from cache if valid, otherwise fetch from API
        
        Args:
            force_refresh: If True, ignore cache and fetch fresh data
            
        Returns:
            List of police station dictionaries
        """
        # If force refresh, skip cache
        if force_refresh:
            logger.info("Force refresh requested, fetching from API...")
            stations = self.fetch_from_overpass()
            
            if stations:
                self.save_to_cache(stations)
                return stations
            else:
                logger.error("Failed to fetch from API, attempting to load from cache")
                # Fall back to cache even if stale
                cached = self.load_from_cache()
                return cached if cached else []
        
        # Check if cache is valid
        if self.is_cache_valid():
            stations = self.load_from_cache()
            if stations is not None:
                return stations
            else:
                logger.warning("Cache load failed, fetching from API...")
        else:
            logger.info("Cache is stale or missing, fetching from API...")
        
        # Cache is invalid or missing, fetch from API
        stations = self.fetch_from_overpass()
        
        if stations:
            self.save_to_cache(stations)
            return stations
        else:
            logger.error("Failed to fetch from API")
            # Try to load from cache anyway (even if stale) as fallback
            cached = self.load_from_cache()
            if cached:
                logger.warning("Using stale cache data as fallback")
                return cached
            else:
                logger.error("No data available - neither from API nor cache")
                return []
    
    def get_cache_info(self) -> Dict:
        """
        Get information about the current cache
        
        Returns:
            Dictionary with cache information
        """
        if not os.path.exists(self.cache_file):
            return {
                'exists': False,
                'valid': False,
                'count': 0
            }
        
        try:
            file_mtime = os.path.getmtime(self.cache_file)
            file_age = datetime.now() - datetime.fromtimestamp(file_mtime)
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'exists': True,
                'valid': self.is_cache_valid(),
                'age_hours': file_age.total_seconds() / 3600,
                'fetched_at': data.get('fetched_at'),
                'count': data.get('count', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {
                'exists': True,
                'valid': False,
                'error': str(e)
            }


# Global instance
_police_data_fetcher = None


def get_police_data_fetcher() -> PoliceDataFetcher:
    """Get or create global police data fetcher instance"""
    global _police_data_fetcher
    if _police_data_fetcher is None:
        _police_data_fetcher = PoliceDataFetcher()
    return _police_data_fetcher


if __name__ == "__main__":
    # Test the fetcher
    logging.basicConfig(level=logging.INFO)
    
    fetcher = PoliceDataFetcher()
    
    print("Fetching police stations data...")
    stations = fetcher.get_police_stations()
    
    print(f"\nTotal stations: {len(stations)}")
    
    if stations:
        print("\nFirst 5 stations:")
        for station in stations[:5]:
            print(f"- {station['name']} ({station['city']}, {station['state']})")
            print(f"  Location: {station['latitude']}, {station['longitude']}")
    
    cache_info = fetcher.get_cache_info()
    print(f"\nCache info: {cache_info}")
