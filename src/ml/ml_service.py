"""
SafeRoute Navigator v2.0 - ML Service
Machine learning service using trained models for hotspot prediction.
Uses real trained models, not demo data.
"""

import pickle
import numpy as np
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class MLService:
    """ML service using trained models for risk prediction."""
    
    def __init__(self):
        """Initialize the ML service with trained models."""
        self.enabled = False
        self.models = {}
        self.feature_info = {}
        logger.info("🤖 ML Service initializing...")
        
        # Load trained models
        self._load_models()
        
        # Load feature information
        self._load_feature_info()
        
        if self.models:
            self.enabled = True
            logger.info(f"✅ ML Service initialized with {len(self.models)} models")
        else:
            logger.warning("⚠️ No trained models found - ML predictions disabled")
    
    def _load_models(self):
        """Load trained ML models from files."""
        model_dir = "models"
        
        if not os.path.exists(model_dir):
            logger.warning(f"Models directory {model_dir} not found")
            return
        
        # Load risk prediction model
        risk_model_path = os.path.join(model_dir, "risk_model.pkl")
        if os.path.exists(risk_model_path):
            try:
                with open(risk_model_path, 'rb') as f:
                    self.models['risk'] = pickle.load(f)
                logger.info("✅ Risk prediction model loaded")
            except Exception as e:
                logger.error(f"Failed to load risk model: {str(e)}")
        
        # Load severity prediction model
        severity_model_path = os.path.join(model_dir, "severity_model.pkl")
        if os.path.exists(severity_model_path):
            try:
                with open(severity_model_path, 'rb') as f:
                    self.models['severity'] = pickle.load(f)
                logger.info("✅ Severity prediction model loaded")
            except Exception as e:
                logger.error(f"Failed to load severity model: {str(e)}")
    
    def _load_feature_info(self):
        """Load feature information for model inputs."""
        feature_info_path = os.path.join("models", "feature_info.pkl")
        
        if os.path.exists(feature_info_path):
            try:
                with open(feature_info_path, 'rb') as f:
                    self.feature_info = pickle.load(f)
                logger.info("✅ Feature information loaded")
            except Exception as e:
                logger.error(f"Failed to load feature info: {str(e)}")
                # Create default feature info if loading fails
                self.feature_info = self._create_default_feature_info()
        else:
            logger.warning("Feature info not found, using defaults")
            self.feature_info = self._create_default_feature_info()
    
    def _create_default_feature_info(self) -> Dict:
        """Create default feature information."""
        return {
            'features': [
                'hour', 'day_of_week', 'month', 'temperature', 'humidity',
                'wind_speed', 'visibility', 'precipitation', 'pressure',
                'traffic_density', 'road_type_highway', 'road_type_arterial',
                'road_type_collector', 'road_type_local', 'weather_condition_numeric',
                'population_density', 'seismic_zone_risk', 'coastal',
                'earthquake_risk', 'tsunami_risk'
            ],
            'categorical_features': ['road_type', 'weather_condition'],
            'numerical_features': [
                'hour', 'day_of_week', 'month', 'temperature', 'humidity',
                'wind_speed', 'visibility', 'precipitation', 'pressure', 'traffic_density',
                'population_density', 'seismic_zone_risk', 'earthquake_risk', 'tsunami_risk'
            ],
            'road_type_mapping': {
                'highway': 0, 'arterial': 1, 'collector': 2, 'local': 3
            },
            'weather_condition_mapping': {
                'clear': 0, 'cloudy': 1, 'rain': 2, 'snow': 3, 'fog': 4, 'storm': 5
            }
        }
    
    def predict_hotspot_risk(self, location_data: Dict) -> Dict:
        """
        Predict hotspot risk using trained ML models.
        
        Args:
            location_data: Dictionary containing location and environmental data
            
        Returns:
            Dict with risk predictions
        """
        try:
            if not self.enabled:
                return {
                    "status": "error",
                    "message": "ML service not available - models not loaded"
                }
            
            # Prepare features for prediction
            features = self._prepare_features(location_data)
            
            predictions = {}
            
            # Risk prediction
            if 'risk' in self.models:
                try:
                    risk_prob = self.models['risk'].predict_proba([features])[0]
                    risk_prediction = self.models['risk'].predict([features])[0]
                    
                    predictions['risk'] = {
                        'probability': float(max(risk_prob)),
                        'prediction': int(risk_prediction),
                        'risk_level': self._map_risk_level(risk_prediction),
                        'confidence': float(max(risk_prob))
                    }
                except Exception as e:
                    logger.error(f"Risk prediction failed: {str(e)}")
                    predictions['risk'] = self._get_fallback_risk_prediction(location_data)
            
            # Severity prediction
            if 'severity' in self.models:
                try:
                    severity_prob = self.models['severity'].predict_proba([features])[0]
                    severity_prediction = self.models['severity'].predict([features])[0]
                    
                    predictions['severity'] = {
                        'probability': float(max(severity_prob)),
                        'prediction': int(severity_prediction),
                        'severity_level': self._map_severity_level(severity_prediction),
                        'confidence': float(max(severity_prob))
                    }
                except Exception as e:
                    logger.error(f"Severity prediction failed: {str(e)}")
                    predictions['severity'] = self._get_fallback_severity_prediction(location_data)
            
            return {
                "status": "success",
                "predictions": predictions,
                "features_used": self.feature_info.get('features', []),
                "model_info": {
                    "models_available": list(self.models.keys()),
                    "prediction_timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"ML prediction error: {str(e)}")
            return {
                "status": "error",
                "message": f"ML prediction failed: {str(e)}"
            }
    
    def _prepare_features(self, location_data: Dict) -> List[float]:
        """Prepare feature vector for ML model input.
        Builds the vector in the exact order expected by loaded feature_info (if available).
        Falls back to a 20-length vector if no model info is present.
        """
        try:
            # Current time features
            now = datetime.now()
            hour = now.hour
            day_of_week = now.weekday()
            month = now.month
            
            # Weather features (from location_data or defaults)
            weather = location_data.get('weather', {})
            temperature = weather.get('temperature_c', 25.0)
            humidity = weather.get('humidity_percent', 60.0)
            wind_speed = weather.get('wind_speed_kmh', 10.0)
            visibility = weather.get('visibility_km', 10.0)
            precipitation = weather.get('precipitation_1h_mm', 0.0)
            pressure = weather.get('pressure_hpa', 1013.0)
            
            # Traffic and location features
            traffic_density = location_data.get('traffic_density', 0.5)  # 0-1 scale
            road_type = location_data.get('road_type', 'arterial')
            
            # Map weather condition to numeric
            weather_condition_num = self._map_weather_condition(weather.get('condition', 'clear'))
            
            # Map road type to one-hot encoding
            road_type_highway = 1 if road_type == 'highway' else 0
            road_type_arterial = 1 if road_type == 'arterial' else 0
            road_type_collector = 1 if road_type == 'collector' else 0
            road_type_local = 1 if road_type == 'local' else 0
            
            # Population density (estimated based on location type)
            population_density = location_data.get('population_density', 1000.0)
            if road_type == 'highway':
                population_density = 500.0
            elif road_type == 'arterial':
                population_density = 1500.0
            elif road_type == 'local':
                population_density = 2000.0
            
            # Disaster risk features (defaults for India)
            seismic_zone_risk = location_data.get('seismic_zone_risk', 3.0)  # 1-5 scale
            coastal = location_data.get('coastal', 0)  # 0 or 1
            earthquake_risk = location_data.get('earthquake_risk', 0.4)  # 0-1 scale
            tsunami_risk = location_data.get('tsunami_risk', 0.2)  # 0-1 scale
            
            # Build a complete feature map
            feature_map = {
                'hour': float(hour),
                'day_of_week': float(day_of_week),
                'month': float(month),
                'temperature': float(temperature),
                'humidity': float(humidity),
                'wind_speed': float(wind_speed),
                'visibility': float(visibility),
                'precipitation': float(precipitation),
                'pressure': float(pressure),
                'traffic_density': float(traffic_density),
                'road_type_highway': float(road_type_highway),
                'road_type_arterial': float(road_type_arterial),
                'road_type_collector': float(road_type_collector),
                'road_type_local': float(road_type_local),
                'weather_condition': float(weather_condition_num),  # alias
                'weather_condition_numeric': float(weather_condition_num),
                'population_density': float(population_density),
                'seismic_zone_risk': float(seismic_zone_risk),
                'coastal': float(coastal),
                'earthquake_risk': float(earthquake_risk),
                'tsunami_risk': float(tsunami_risk),
            }
            
            # If feature_info defines expected order/length, follow it
            expected_features = self.feature_info.get('features') if isinstance(self.feature_info, dict) else None
            if expected_features:
                features = [feature_map.get(name, 0.0) for name in expected_features]
                return features
            
            # Fallback: Create 20-length vector
            features = [
                feature_map['hour'], feature_map['day_of_week'], feature_map['month'],
                feature_map['temperature'], feature_map['humidity'],
                feature_map['wind_speed'], feature_map['visibility'], feature_map['precipitation'], feature_map['pressure'],
                feature_map['traffic_density'],
                feature_map['road_type_highway'], feature_map['road_type_arterial'], feature_map['road_type_collector'], feature_map['road_type_local'],
                feature_map['weather_condition_numeric'], feature_map['population_density'],
                feature_map['seismic_zone_risk'], feature_map['coastal'], feature_map['earthquake_risk'], feature_map['tsunami_risk']
            ]
            return features
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {str(e)}")
            # Return default features if preparation fails (match minimal 16-feature set)
            return [12, 2, 6, 25.0, 60.0, 10.0, 10.0, 0.0, 1013.0, 0.5, 0, 1, 0, 0, 0, 1000.0]
    
    def _map_weather_condition(self, condition: str) -> int:
        """Map weather condition string to numeric value."""
        condition_lower = condition.lower()
        
        if 'clear' in condition_lower or 'sun' in condition_lower:
            return self.feature_info['weather_condition_mapping'].get('clear', 0)
        elif 'cloud' in condition_lower:
            return self.feature_info['weather_condition_mapping'].get('cloudy', 1)
        elif 'rain' in condition_lower or 'drizzle' in condition_lower:
            return self.feature_info['weather_condition_mapping'].get('rain', 2)
        elif 'snow' in condition_lower or 'sleet' in condition_lower:
            return self.feature_info['weather_condition_mapping'].get('snow', 3)
        elif 'fog' in condition_lower or 'mist' in condition_lower:
            return self.feature_info['weather_condition_mapping'].get('fog', 4)
        elif 'storm' in condition_lower or 'thunder' in condition_lower:
            return self.feature_info['weather_condition_mapping'].get('storm', 5)
        else:
            return 0  # Default to clear
    
    def _map_risk_level(self, risk_prediction: int) -> str:
        """Map numeric risk prediction to risk level."""
        risk_mapping = {0: 'low', 1: 'medium', 2: 'high', 3: 'critical'}
        return risk_mapping.get(risk_prediction, 'medium')
    
    def _map_severity_level(self, severity_prediction: int) -> str:
        """Map numeric severity prediction to severity level."""
        severity_mapping = {0: 'minor', 1: 'moderate', 2: 'severe', 3: 'critical'}
        return severity_mapping.get(severity_prediction, 'moderate')
    
    def _get_fallback_risk_prediction(self, location_data: Dict) -> Dict:
        """Generate fallback risk prediction when ML model fails."""
        # Simple rule-based fallback
        weather = location_data.get('weather', {})
        risk_score = 0.5  # Base risk
        
        # Adjust based on weather
        condition = weather.get('condition', '').lower()
        if any(term in condition for term in ['storm', 'heavy', 'extreme']):
            risk_score = 0.8
        elif any(term in condition for term in ['rain', 'snow', 'fog']):
            risk_score = 0.6
        elif 'clear' in condition:
            risk_score = 0.3
        
        # Adjust based on time
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
            risk_score += 0.1
        elif 22 <= hour or hour <= 5:  # Night time
            risk_score += 0.1
        
        risk_score = min(1.0, max(0.0, risk_score))
        
        if risk_score < 0.3:
            risk_level = 'low'
            prediction = 0
        elif risk_score < 0.6:
            risk_level = 'medium'
            prediction = 1
        elif risk_score < 0.8:
            risk_level = 'high'
            prediction = 2
        else:
            risk_level = 'critical'
            prediction = 3
        
        return {
            'probability': risk_score,
            'prediction': prediction,
            'risk_level': risk_level,
            'confidence': 0.7,  # Lower confidence for fallback
            'fallback': True
        }
    
    def _get_fallback_severity_prediction(self, location_data: Dict) -> Dict:
        """Generate fallback severity prediction when ML model fails."""
        # Simple rule-based fallback
        weather = location_data.get('weather', {})
        severity_score = 0.4  # Base severity
        
        # Adjust based on weather
        condition = weather.get('condition', '').lower()
        if any(term in condition for term in ['extreme', 'severe', 'heavy']):
            severity_score = 0.8
        elif any(term in condition for term in ['moderate', 'rain', 'snow']):
            severity_score = 0.6
        
        severity_score = min(1.0, max(0.0, severity_score))
        
        if severity_score < 0.3:
            severity_level = 'minor'
            prediction = 0
        elif severity_score < 0.6:
            severity_level = 'moderate'
            prediction = 1
        elif severity_score < 0.8:
            severity_level = 'severe'
            prediction = 2
        else:
            severity_level = 'critical'
            prediction = 3
        
        return {
            'probability': severity_score,
            'prediction': prediction,
            'severity_level': severity_level,
            'confidence': 0.6,  # Lower confidence for fallback
            'fallback': True
        }
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models."""
        return {
            "status": "success" if self.enabled else "disabled",
            "models_loaded": list(self.models.keys()),
            "model_count": len(self.models),
            "features_available": self.feature_info.get('features', []),
            "feature_count": len(self.feature_info.get('features', [])),
            "service_enabled": self.enabled
        }
    
    def predict_batch_hotspots(self, locations_data: List[Dict]) -> Dict:
        """
        Predict risks for multiple locations in batch.
        
        Args:
            locations_data: List of location dictionaries
            
        Returns:
            Dict with batch predictions
        """
        try:
            if not self.enabled:
                return {
                    "status": "error",
                    "message": "ML service not available"
                }
            
            batch_predictions = []
            
            for i, location_data in enumerate(locations_data):
                try:
                    prediction = self.predict_hotspot_risk(location_data)
                    prediction['location_index'] = i
                    prediction['location_id'] = location_data.get('id', f'location_{i}')
                    batch_predictions.append(prediction)
                except Exception as e:
                    logger.error(f"Batch prediction failed for location {i}: {str(e)}")
                    batch_predictions.append({
                        "status": "error",
                        "message": f"Prediction failed: {str(e)}",
                        "location_index": i,
                        "location_id": location_data.get('id', f'location_{i}')
                    })
            
            return {
                "status": "success",
                "batch_predictions": batch_predictions,
                "total_locations": len(locations_data),
                "successful_predictions": len([p for p in batch_predictions if p.get("status") == "success"]),
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch ML prediction error: {str(e)}")
            return {
                "status": "error",
                "message": f"Batch ML prediction failed: {str(e)}"
            }

# Global instance
ml_service = MLService()