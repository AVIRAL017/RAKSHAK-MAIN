"""
Start the application and verify emergency features are working
"""

import sys
import time
import requests
from colorama import init, Fore, Style

init(autoreset=True)

def print_header(text):
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'=' * 60}\n")

def print_success(text):
    print(f"{Fore.GREEN}✓ {text}")

def print_error(text):
    print(f"{Fore.RED}✗ {text}")

def print_warning(text):
    print(f"{Fore.YELLOW}⚠ {text}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ {text}")

def verify_emergency_system():
    """Verify emergency system is working"""
    
    print_header("🚑 Emergency Response System Verification")
    
    base_url = "http://127.0.0.1:5000"
    
    # Test 1: Check if server is running
    print_info("Testing if server is running...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print_success("Server is running!")
        else:
            print_error(f"Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Server is not running. Please start it with: python run.py")
        return False
    except Exception as e:
        print_error(f"Error connecting to server: {e}")
        return False
    
    # Test 2: Check hospitals API
    print_info("\nTesting Hospitals API...")
    try:
        response = requests.get(f"{base_url}/api/emergency/hospitals?limit=5", timeout=10)
        data = response.json()
        if data.get('status') == 'success':
            count = data['data']['count']
            print_success(f"Hospitals API working! Loaded {count} hospitals")
            if count > 0:
                sample = data['data']['hospitals'][0]
                print_info(f"  Sample: {sample['name']} - {sample['district']}, {sample['state']}")
        else:
            print_error("Hospitals API returned error")
    except Exception as e:
        print_error(f"Hospitals API failed: {e}")
    
    # Test 3: Check ambulances API
    print_info("\nTesting Ambulances API...")
    try:
        response = requests.get(f"{base_url}/api/emergency/ambulances?recalculate=true", timeout=15)
        data = response.json()
        if data.get('status') == 'success':
            count = data['data']['count']
            print_success(f"Ambulances API working! Calculated {count} placements")
            if count > 0:
                sample = data['data']['ambulances'][0]
                print_info(f"  Sample: {sample['hotspot_name']} → {sample['assigned_hospital']['name']} ({sample['distance_to_hospital']} km)")
        else:
            print_error("Ambulances API returned error")
    except Exception as e:
        print_error(f"Ambulances API failed: {e}")
    
    # Test 4: Check if JavaScript file is accessible
    print_info("\nTesting JavaScript files...")
    try:
        response = requests.get(f"{base_url}/static/js/emergency-layers.js", timeout=5)
        if response.status_code == 200:
            print_success("emergency-layers.js is accessible")
            # Check if it contains key functions
            content = response.text
            if 'EmergencyLayers' in content:
                print_success("EmergencyLayers object found in JavaScript")
            if 'createHospitalIcon' in content:
                print_success("Hospital icon creator found")
            if 'createAmbulanceIcon' in content:
                print_success("Ambulance icon creator found")
        else:
            print_error("emergency-layers.js not accessible")
    except Exception as e:
        print_error(f"JavaScript file check failed: {e}")
    
    # Final instructions
    print_header("📋 Next Steps")
    print(f"{Fore.WHITE}1. Open your browser to: {Fore.CYAN}http://127.0.0.1:5000")
    print(f"{Fore.WHITE}2. Do a HARD REFRESH: {Fore.YELLOW}Ctrl + Shift + R{Fore.WHITE} (or {Fore.YELLOW}Ctrl + F5{Fore.WHITE})")
    print(f"{Fore.WHITE}3. Wait 30-60 seconds for all data to load")
    print(f"{Fore.WHITE}4. Look for these features:")
    print(f"{Fore.WHITE}   • Layer control menu in top-right corner (purple header)")
    print(f"{Fore.WHITE}   • Red hospital markers (plus sign icons)")
    print(f"{Fore.WHITE}   • Orange ambulance markers (pulsing)")
    print(f"{Fore.WHITE}5. Open browser console (F12) and type: {Fore.CYAN}window.EmergencyLayers")
    print(f"{Fore.WHITE}   Should show an object, not 'undefined'")
    
    print(f"\n{Fore.GREEN}If you still don't see features, open the test page:")
    print(f"{Fore.CYAN}http://127.0.0.1:5000/static/test_emergency.html\n")
    
    return True

if __name__ == '__main__':
    print(f"\n{Fore.MAGENTA}{'*' * 60}")
    print(f"{Fore.MAGENTA}  RAKSHAK - Emergency Response System Verification")
    print(f"{Fore.MAGENTA}{'*' * 60}")
    
    print_info("\nMake sure the application is running (python run.py)")
    print_info("This script will verify all emergency features...\n")
    
    time.sleep(1)
    verify_emergency_system()
