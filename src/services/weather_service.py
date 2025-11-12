"""
SafeRoute Navigator v2.0 - Weather Service
Real weather service using OpenWeatherMap API.
API Key source: environment variable OPENWEATHER_API_KEY (preferred) with safe fallback.
"""

import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    """Real weather service using OpenWeatherMap API."""
    
    def __init__(self):
        """Initialize the weather service."""
        self.enabled = True
        # Prefer environment variable; fallback to existing application key
        fallback_key = "979e8abfd8f82adc7a27725a7f7136eb"
        self.api_key = os.getenv("OPENWEATHER_API_KEY", fallback_key)
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SafeRoute Navigator v2.0'})
        masked = self.api_key[:4] + "…" + self.api_key[-4:] if self.api_key else "missing"
        logger.info(f"✅ Weather Service initialized (API key: {masked})")
        
        # Cache for weather data (reduce API calls)
        self.cache = {}
        self.cache_duration = 600  # 10 minutes
        
        # Driving impact mappings based on OpenWeatherMap conditions
        self.condition_impacts = {
            # Clear conditions (2xx)
            "clear sky": {"risk_factor": 0.0, "impact": "none", "speed_reduction": 0},
            "few clouds": {"risk_factor": 0.05, "impact": "minimal", "speed_reduction": 0},
            "scattered clouds": {"risk_factor": 0.1, "impact": "minimal", "speed_reduction": 5},
            "broken clouds": {"risk_factor": 0.15, "impact": "minimal", "speed_reduction": 5},
            "overcast clouds": {"risk_factor": 0.2, "impact": "minimal", "speed_reduction": 10},
            
            # Drizzle (3xx)
            "light intensity drizzle": {"risk_factor": 0.25, "impact": "moderate", "speed_reduction": 10},
            "drizzle": {"risk_factor": 0.3, "impact": "moderate", "speed_reduction": 15},
            "heavy intensity drizzle": {"risk_factor": 0.35, "impact": "moderate", "speed_reduction": 20},
            
            # Rain (5xx)
            "light rain": {"risk_factor": 0.3, "impact": "moderate", "speed_reduction": 15},
            "moderate rain": {"risk_factor": 0.5, "impact": "significant", "speed_reduction": 25},
            "heavy intensity rain": {"risk_factor": 0.7, "impact": "severe", "speed_reduction": 40},
            "very heavy rain": {"risk_factor": 0.85, "impact": "severe", "speed_reduction": 50},
            "extreme rain": {"risk_factor": 0.95, "impact": "extreme", "speed_reduction": 70},
            "shower rain": {"risk_factor": 0.4, "impact": "moderate", "speed_reduction": 20},
            "heavy intensity shower rain": {"risk_factor": 0.75, "impact": "severe", "speed_reduction": 45},
            "ragged shower rain": {"risk_factor": 0.45, "impact": "moderate", "speed_reduction": 25},
            
            # Snow (6xx)
            "light snow": {"risk_factor": 0.6, "impact": "significant", "speed_reduction": 30},
            "snow": {"risk_factor": 0.8, "impact": "severe", "speed_reduction": 50},
            "heavy snow": {"risk_factor": 0.9, "impact": "extreme", "speed_reduction": 60},
            "sleet": {"risk_factor": 0.85, "impact": "severe", "speed_reduction": 55},
            "light shower sleet": {"risk_factor": 0.7, "impact": "severe", "speed_reduction": 35},
            "shower sleet": {"risk_factor": 0.8, "impact": "severe", "speed_reduction": 45},
            "light rain and snow": {"risk_factor": 0.75, "impact": "severe", "speed_reduction": 40},
            "rain and snow": {"risk_factor": 0.85, "impact": "severe", "speed_reduction": 50},
            "light shower snow": {"risk_factor": 0.65, "impact": "significant", "speed_reduction": 35},
            "shower snow": {"risk_factor": 0.8, "impact": "severe", "speed_reduction": 50},
            "heavy shower snow": {"risk_factor": 0.9, "impact": "extreme", "speed_reduction": 60},
            
            # Atmospheric conditions (7xx)
            "mist": {"risk_factor": 0.4, "impact": "moderate", "speed_reduction": 20},
            "smoke": {"risk_factor": 0.5, "impact": "significant", "speed_reduction": 25},
            "haze": {"risk_factor": 0.3, "impact": "moderate", "speed_reduction": 15},
            "sand/dust whirls": {"risk_factor": 0.6, "impact": "significant", "speed_reduction": 30},
            "fog": {"risk_factor": 0.9, "impact": "extreme", "speed_reduction": 60},
            "sand": {"risk_factor": 0.7, "impact": "severe", "speed_reduction": 40},
            "dust": {"risk_factor": 0.6, "impact": "significant", "speed_reduction": 30},
            "volcanic ash": {"risk_factor": 0.95, "impact": "extreme", "speed_reduction": 70},
            "squalls": {"risk_factor": 0.9, "impact": "extreme", "speed_reduction": 65},
            "tornado": {"risk_factor": 1.0, "impact": "extreme", "speed_reduction": 100},
            
            # Thunderstorm (2xx)
            "thunderstorm with light rain": {"risk_factor": 0.8, "impact": "severe", "speed_reduction": 45},
            "thunderstorm with rain": {"risk_factor": 0.85, "impact": "severe", "speed_reduction": 50},
            "thunderstorm with heavy rain": {"risk_factor": 0.95, "impact": "extreme", "speed_reduction": 70},
            "light thunderstorm": {"risk_factor": 0.75, "impact": "severe", "speed_reduction": 40},
            "thunderstorm": {"risk_factor": 0.85, "impact": "severe", "speed_reduction": 50},
            "heavy thunderstorm": {"risk_factor": 0.95, "impact": "extreme", "speed_reduction": 70},
            "ragged thunderstorm": {"risk_factor": 0.8, "impact": "severe", "speed_reduction": 45},
            "thunderstorm with light drizzle": {"risk_factor": 0.75, "impact": "severe", "speed_reduction": 40},
            "thunderstorm with drizzle": {"risk_factor": 0.8, "impact": "severe", "speed_reduction": 45},
            "thunderstorm with heavy drizzle": {"risk_factor": 0.9, "impact": "extreme", "speed_reduction": 60}
        }
    
    def get_current_weather(self, lat: float, lng: float) -> Dict:
        """Get current weather data for location from OpenWeatherMap."""
        try:
            # Check cache first
            cache_key = f"current_{lat}_{lng}"
            if self._is_cached_valid(cache_key):
                logger.info("Using cached weather data")
                return self.cache[cache_key]['data']
            
            # Make API request
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Extract relevant data
            condition = weather_data['weather'][0]['description'].lower()
            condition_impact = self.condition_impacts.get(condition, {
                "risk_factor": 0.2, "impact": "moderate", "speed_reduction": 10
            })
            
            result = {
                "status": "success",
                "data": {
                    "location": {
                        "latitude": lat,
                        "longitude": lng,
                        "city": weather_data.get('name', 'Unknown'),
                        "country": weather_data.get('sys', {}).get('country', 'Unknown')
                    },
                    "current": {
                        "condition": condition,
                        "description": weather_data['weather'][0]['description'],
                        "icon": weather_data['weather'][0]['icon'],
                        "temperature_c": round(weather_data['main']['temp'], 1),
                        "feels_like_c": round(weather_data['main']['feels_like'], 1),
                        "humidity_percent": weather_data['main']['humidity'],
                        "pressure_hpa": weather_data['main']['pressure'],
                        "visibility_m": weather_data.get('visibility', 10000),
                        "visibility_km": round(weather_data.get('visibility', 10000) / 1000, 1),
                        "wind_speed_kmh": round(weather_data.get('wind', {}).get('speed', 0) * 3.6, 1),
                        "wind_direction_deg": weather_data.get('wind', {}).get('deg', 0),
                        "wind_direction": self._degrees_to_compass(weather_data.get('wind', {}).get('deg', 0)),
                        "clouds_percent": weather_data.get('clouds', {}).get('all', 0),
                        "precipitation_1h_mm": (
                            weather_data.get('rain', {}).get('1h', 0) + 
                            weather_data.get('snow', {}).get('1h', 0)
                        ),
                        "sunrise": datetime.fromtimestamp(weather_data['sys']['sunrise']).isoformat(),
                        "sunset": datetime.fromtimestamp(weather_data['sys']['sunset']).isoformat()
                    },
                    "driving_conditions": {
                        "risk_factor": condition_impact["risk_factor"],
                        "impact_level": condition_impact["impact"],
                        "recommended_speed_reduction": condition_impact["speed_reduction"],
                        "recommendations": self._get_driving_recommendations(condition, condition_impact),
                        "safety_alerts": self._get_safety_alerts(weather_data, condition_impact)
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "OpenWeatherMap"
                }
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': result,
                'timestamp': datetime.utcnow()
            }
            
            logger.info(f"Retrieved weather data for {weather_data.get('name', 'location')}: {condition}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API request failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to retrieve weather data: {str(e)}",
                "fallback": "Check internet connection and API key"
            }
        except Exception as e:
            logger.error(f"Weather data processing error: {str(e)}")
            return {
                "status": "error",
                "message": f"Weather data processing failed: {str(e)}"
            }
    
    def get_weather_forecast(self, lat: float, lng: float, days: int = 5) -> Dict:
        """Get weather forecast for location from OpenWeatherMap."""
        try:
            # Check cache first
            cache_key = f"forecast_{lat}_{lng}_{days}"
            if self._is_cached_valid(cache_key):
                logger.info("Using cached forecast data")
                return self.cache[cache_key]['data']
            
            # Make API request for 5-day forecast
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            forecast_data = response.json()
            
            # Process forecast data (groups by day)
            daily_forecasts = self._process_forecast_data(forecast_data, days)
            
            result = {
                "status": "success",
                "data": {
                    "location": {
                        "latitude": lat,
                        "longitude": lng,
                        "city": forecast_data['city']['name'],
                        "country": forecast_data['city']['country']
                    },
                    "forecast": daily_forecasts,
                    "generated_at": datetime.utcnow().isoformat(),
                    "source": "OpenWeatherMap"
                }
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': result,
                'timestamp': datetime.utcnow()
            }
            
            logger.info(f"Retrieved {days}-day forecast for {forecast_data['city']['name']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather forecast API request failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to retrieve weather forecast: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Weather forecast processing error: {str(e)}")
            return {
                "status": "error",
                "message": f"Weather forecast processing failed: {str(e)}"
            }
    
    def get_weather_alerts(self, lat: float, lng: float) -> Dict:
        """Get weather alerts for location."""
        try:
            # Check cache first
            cache_key = f"alerts_{lat}_{lng}"
            if self._is_cached_valid(cache_key):
                logger.info("Using cached weather alerts")
                return self.cache[cache_key]['data']
            
            # Generate basic alerts from current weather (OpenWeatherMap free tier limitation)
            current_weather = self.get_current_weather(lat, lng)
            alerts = self._generate_basic_alerts(current_weather)
            
            result = {
                "status": "success",
                "data": {
                    "location": {"latitude": lat, "longitude": lng},
                    "alerts": alerts,
                    "alert_count": len(alerts),
                    "generated_at": datetime.utcnow().isoformat(),
                    "source": "OpenWeatherMap (Basic Alerts)"
                }
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': result,
                'timestamp': datetime.utcnow()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Weather alerts error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to retrieve weather alerts: {str(e)}"
            }
    
    def _is_cached_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return (datetime.utcnow() - cached_time).seconds < self.cache_duration
    
    def _degrees_to_compass(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction."""
        if degrees is None:
            return "Unknown"
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _process_forecast_data(self, forecast_data: Dict, days: int) -> List[Dict]:
        """Process raw forecast data into daily summaries."""
        daily_forecasts = []
        current_date = None
        daily_data = {}
        
        for item in forecast_data['list'][:days * 8]:  # 8 items per day (3-hour intervals)
            forecast_time = datetime.fromtimestamp(item['dt'])
            date_str = forecast_time.strftime('%Y-%m-%d')
            
            if current_date != date_str:
                if current_date:
                    # Process previous day
                    daily_forecasts.append(self._create_daily_summary(current_date, daily_data))
                
                current_date = date_str
                daily_data = {'items': [], 'temps': [], 'conditions': []}
            
            daily_data['items'].append(item)
            daily_data['temps'].append(item['main']['temp'])
            daily_data['conditions'].append(item['weather'][0]['description'].lower())
        
        # Process last day
        if current_date and daily_data['items']:
            daily_forecasts.append(self._create_daily_summary(current_date, daily_data))
        
        return daily_forecasts[:days]
    
    def _create_daily_summary(self, date_str: str, daily_data: Dict) -> Dict:
        """Create daily forecast summary from hourly data."""
        temps = daily_data['temps']
        conditions = daily_data['conditions']
        items = daily_data['items']
        
        # Most frequent condition
        most_common_condition = max(set(conditions), key=conditions.count)
        condition_impact = self.condition_impacts.get(most_common_condition, {
            "risk_factor": 0.2, "impact": "moderate", "speed_reduction": 10
        })
        
        # Calculate precipitation
        precipitation = sum([
            item.get('rain', {}).get('3h', 0) + item.get('snow', {}).get('3h', 0)
            for item in items
        ])
        
        return {
            "date": date_str,
            "day_of_week": datetime.strptime(date_str, '%Y-%m-%d').strftime('%A'),
            "condition": most_common_condition,
            "description": most_common_condition.title(),
            "temperature_high_c": round(max(temps), 1),
            "temperature_low_c": round(min(temps), 1),
            "humidity_percent": round(sum([item['main']['humidity'] for item in items]) / len(items)),
            "wind_speed_kmh": round(sum([item.get('wind', {}).get('speed', 0) for item in items]) / len(items) * 3.6, 1),
            "precipitation_mm": round(precipitation, 1),
            "precipitation_chance": len([c for c in conditions if 'rain' in c or 'snow' in c]) * 100 // len(conditions),
            "driving_risk": condition_impact["risk_factor"],
            "visibility_impact": "reduced" if condition_impact["risk_factor"] > 0.3 else "normal"
        }
    
    def _get_driving_recommendations(self, condition: str, impact: Dict) -> List[str]:
        """Get driving recommendations based on weather condition."""
        recommendations = []
        risk_factor = impact["risk_factor"]
        
        if risk_factor == 0.0:
            recommendations.extend([
                "Excellent driving conditions",
                "Normal speed limits apply",
                "Watch for glare during sunrise/sunset hours"
            ])
        elif risk_factor <= 0.2:
            recommendations.extend([
                "Generally good driving conditions",
                "Be aware of changing light conditions",
                "Consider using headlights during overcast conditions"
            ])
        elif risk_factor <= 0.4:
            recommendations.extend([
                f"Reduce speed by {impact['speed_reduction']}%",
                "Increase following distance",
                "Use headlights for better visibility",
                "Be prepared for slippery road conditions"
            ])
        elif risk_factor <= 0.6:
            recommendations.extend([
                f"Reduce speed by {impact['speed_reduction']}%",
                "Significantly increase following distance",
                "Use headlights and consider hazard lights in poor visibility",
                "Avoid sudden maneuvers and hard braking"
            ])
        elif risk_factor <= 0.8:
            recommendations.extend([
                f"Reduce speed by {impact['speed_reduction']}%",
                "Consider delaying non-essential travel",
                "Use low-beam headlights (avoid high beams in fog)",
                "Keep emergency supplies and communication devices ready"
            ])
        else:
            recommendations.extend([
                "Avoid travel if possible - dangerous conditions",
                "If driving is absolutely necessary, reduce speed significantly",
                "Pull over safely if conditions worsen",
                "Inform others of your travel plans and expected arrival"
            ])
        
        # Condition-specific recommendations
        if "rain" in condition or "drizzle" in condition:
            recommendations.extend([
                "Watch for hydroplaning on wet roads",
                "Test brakes gently after driving through standing water",
                "Avoid flooded roads - turn around, don't drown"
            ])
        elif "snow" in condition or "sleet" in condition:
            recommendations.extend([
                "Use winter tires or chains if available",
                "Clear all snow and ice from vehicle before driving",
                "Allow extra time for vehicle warm-up and travel"
            ])
        elif "fog" in condition or "mist" in condition:
            recommendations.extend([
                "Follow road markings and reflectors closely",
                "Use fog lights or low-beam headlights",
                "Avoid passing other vehicles"
            ])
        elif "thunderstorm" in condition:
            recommendations.extend([
                "Avoid parking under trees or power lines",
                "Stay in vehicle during lightning activity",
                "Watch for flash flooding and hail"
            ])
        elif "dust" in condition or "sand" in condition:
            recommendations.extend([
                "Close windows and use recirculated air",
                "Change air filters after dust storms",
                "Be aware of sudden visibility changes"
            ])
        
        return recommendations
    
    def _get_safety_alerts(self, weather_data: Dict, impact: Dict) -> List[str]:
        """Generate safety alerts based on weather conditions."""
        alerts = []
        
        # Visibility alerts
        visibility = weather_data.get('visibility', 10000)
        if visibility < 500:
            alerts.append("DANGER: Extremely low visibility - avoid travel")
        elif visibility < 1000:
            alerts.append("WARNING: Very low visibility - extreme caution required")
        elif visibility < 5000:
            alerts.append("CAUTION: Reduced visibility - use headlights")
        
        # Wind alerts
        wind_speed = weather_data.get('wind', {}).get('speed', 0) * 3.6  # Convert to km/h
        if wind_speed > 70:
            alerts.append("DANGER: Extreme winds - avoid driving high-profile vehicles")
        elif wind_speed > 50:
            alerts.append("WARNING: Strong winds - watch for vehicle instability")
        elif wind_speed > 30:
            alerts.append("CAUTION: Moderate winds - be careful on bridges and open areas")
        
        # Temperature alerts
        temp = weather_data['main']['temp']
        if temp <= -10:
            alerts.append("DANGER: Extreme cold - risk of vehicle breakdown")
        elif temp <= 0:
            alerts.append("WARNING: Freezing conditions - watch for ice on roads")
        elif temp >= 45:
            alerts.append("DANGER: Extreme heat - risk of vehicle overheating")
        elif temp >= 40:
            alerts.append("WARNING: Very hot conditions - monitor vehicle temperature")
        
        # Precipitation alerts
        precipitation = weather_data.get('rain', {}).get('1h', 0) + weather_data.get('snow', {}).get('1h', 0)
        if precipitation > 25:
            alerts.append("DANGER: Heavy precipitation - severe flooding risk")
        elif precipitation > 10:
            alerts.append("WARNING: Moderate to heavy precipitation - flooding possible")
        
        # High impact weather alerts
        if impact["risk_factor"] >= 0.9:
            alerts.append("EMERGENCY: Extremely dangerous driving conditions")
        elif impact["risk_factor"] >= 0.7:
            alerts.append("WARNING: Dangerous driving conditions - consider postponing travel")
        
        return alerts
    
    def _generate_basic_alerts(self, current_weather: Dict) -> List[Dict]:
        """Generate basic alerts from current weather data."""
        alerts = []
        
        if current_weather.get("status") != "success":
            return alerts
        
        driving_conditions = current_weather["data"]["driving_conditions"]
        current = current_weather["data"]["current"]
        
        # High risk condition alert
        if driving_conditions["risk_factor"] >= 0.7:
            alerts.append({
                "id": f"severe_weather_{int(datetime.now().timestamp())}",
                "type": "severe_weather_warning",
                "severity": "high" if driving_conditions["risk_factor"] >= 0.8 else "moderate",
                "title": "Severe Weather Warning",
                "description": f"Current conditions ({current['description']}) create dangerous driving conditions with {driving_conditions['recommended_speed_reduction']}% speed reduction recommended.",
                "issued_at": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(hours=6)).isoformat(),
                "source": "OpenWeatherMap Analysis",
                "recommendations": driving_conditions["recommendations"][:3]  # Top 3 recommendations
            })
        
        # Low visibility alert
        if current["visibility_km"] < 1:
            alerts.append({
                "id": f"visibility_alert_{int(datetime.now().timestamp())}",
                "type": "low_visibility_warning",
                "severity": "high" if current["visibility_km"] < 0.5 else "moderate",
                "title": "Low Visibility Warning",
                "description": f"Visibility severely reduced to {current['visibility_km']} km due to {current['description']}.",
                "issued_at": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
                "source": "OpenWeatherMap Analysis",
                "recommendations": [
                    "Use fog lights or low-beam headlights",
                    "Reduce speed significantly",
                    "Increase following distance",
                    "Consider delaying travel if possible"
                ]
            })
        
        # High wind alert
        if current["wind_speed_kmh"] > 50:
            alerts.append({
                "id": f"wind_alert_{int(datetime.now().timestamp())}",
                "type": "high_wind_warning",
                "severity": "high" if current["wind_speed_kmh"] > 70 else "moderate",
                "title": "High Wind Warning",
                "description": f"Strong winds at {current['wind_speed_kmh']} km/h from {current['wind_direction']} direction.",
                "issued_at": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
                "source": "OpenWeatherMap Analysis",
                "recommendations": [
                    "Avoid driving high-profile vehicles",
                    "Be cautious on bridges and open areas",
                    "Maintain firm grip on steering wheel",
                    "Watch for debris on roadways"
                ]
            })
        
        # Temperature extreme alerts
        temp = current["temperature_c"]
        if temp <= 0:
            alerts.append({
                "id": f"freeze_alert_{int(datetime.now().timestamp())}",
                "type": "freezing_conditions_warning",
                "severity": "moderate",
                "title": "Freezing Conditions Alert",
                "description": f"Temperature at {temp}°C - risk of ice formation on roads.",
                "issued_at": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
                "source": "OpenWeatherMap Analysis",
                "recommendations": [
                    "Watch for black ice on roads",
                    "Allow extra time for travel",
                    "Ensure vehicle is winter-ready",
                    "Drive slowly on bridges and overpasses"
                ]
            })
        elif temp >= 40:
            alerts.append({
                "id": f"heat_alert_{int(datetime.now().timestamp())}",
                "type": "extreme_heat_advisory",
                "severity": "moderate",
                "title": "Extreme Heat Advisory",
                "description": f"Temperature at {temp}°C - risk of vehicle overheating.",
                "issued_at": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
                "source": "OpenWeatherMap Analysis",
                "recommendations": [
                    "Check vehicle cooling system",
                    "Carry extra water for emergencies",
                    "Avoid leaving anyone in parked vehicle",
                    "Monitor engine temperature gauge"
                ]
            })
        
        return alerts

# Global instance
weather_service = WeatherService()