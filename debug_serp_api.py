#!/usr/bin/env python3
"""
Debug script to understand SERP API response format
"""

import requests
import json

def test_serp_api():
    """Test SERP API with different parameter combinations."""
    api_key = "47822c10820964ca615b5359b528ce4ecc72fba8309ff6cc3f8d14b8ec2514a0"
    base_url = "https://serpapi.com/search.json"
    
    # Test different parameter combinations
    test_cases = [
        {
            'name': 'Google Maps Search',
            'params': {
                'engine': 'google_maps',
                'api_key': api_key,
                'q': 'directions from Delhi to Mumbai',
                'type': 'search'
            }
        },
        {
            'name': 'Google Maps Places',
            'params': {
                'engine': 'google_maps',
                'api_key': api_key,
                'll': '@28.6139,77.2090,15z',
                'q': 'restaurants',
                'type': 'search'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*50}")
        print(f"Testing: {test_case['name']}")
        print(f"{'='*50}")
        
        try:
            response = requests.get(base_url, params=test_case['params'], timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                # Show some sample data
                if 'local_results' in data:
                    print(f"Local results found: {len(data['local_results'])}")
                if 'search_metadata' in data:
                    print(f"Search ID: {data['search_metadata'].get('id', 'N/A')}")
                if 'search_information' in data:
                    print(f"Total results: {data['search_information'].get('total_results', 'N/A')}")
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    test_serp_api()