#!/usr/bin/env python3
"""
SafeRoute Navigator - ML Model Fixer
Fix ML model feature mismatch issues by creating properly sized dummy models
"""

import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_working_models():
    """Create working ML models with correct feature sizes."""
    
    # Ensure models directory exists
    os.makedirs('models', exist_ok=True)
    
    # Define the correct feature set (16 features total)
    feature_info = {
        'features': [
            # Time features (3)
            'hour', 'day_of_week', 'month',
            # Weather features (6) 
            'temperature', 'humidity', 'wind_speed', 'visibility', 'precipitation', 'pressure',
            # Location features (7)
            'traffic_density', 'road_type_highway', 'road_type_arterial', 'road_type_collector', 'road_type_local',
            'weather_condition_numeric', 'population_density'
        ],
        'categorical_features': ['road_type', 'weather_condition'],
        'numerical_features': [
            'hour', 'day_of_week', 'month', 'temperature', 'humidity',
            'wind_speed', 'visibility', 'precipitation', 'pressure', 'traffic_density', 'population_density'
        ],
        'road_type_mapping': {
            'highway': 0, 'arterial': 1, 'collector': 2, 'local': 3
        },
        'weather_condition_mapping': {
            'clear': 0, 'cloudy': 1, 'rain': 2, 'snow': 3, 'fog': 4, 'storm': 5
        }
    }
    
    # Generate sample training data (16 features)
    np.random.seed(42)
    n_samples = 1000
    
    # Create synthetic training data
    X_train = np.random.randn(n_samples, 16)
    
    # Make the data more realistic
    X_train[:, 0] = np.random.randint(0, 24, n_samples)  # hour
    X_train[:, 1] = np.random.randint(0, 7, n_samples)   # day_of_week
    X_train[:, 2] = np.random.randint(1, 13, n_samples)  # month
    X_train[:, 3] = np.random.normal(20, 10, n_samples)  # temperature
    X_train[:, 4] = np.random.uniform(30, 90, n_samples) # humidity
    X_train[:, 5] = np.random.uniform(0, 30, n_samples)  # wind_speed
    X_train[:, 6] = np.random.uniform(1, 20, n_samples)  # visibility
    X_train[:, 7] = np.random.exponential(2, n_samples)  # precipitation
    X_train[:, 8] = np.random.normal(1013, 20, n_samples) # pressure
    X_train[:, 9] = np.random.uniform(0, 1, n_samples)   # traffic_density
    X_train[:, 10] = np.random.binomial(1, 0.2, n_samples) # road_type_highway
    X_train[:, 11] = np.random.binomial(1, 0.3, n_samples) # road_type_arterial
    X_train[:, 12] = np.random.binomial(1, 0.3, n_samples) # road_type_collector
    X_train[:, 13] = np.random.binomial(1, 0.2, n_samples) # road_type_local
    X_train[:, 14] = np.random.randint(0, 6, n_samples)  # weather_condition_numeric
    X_train[:, 15] = np.random.uniform(100, 5000, n_samples) # population_density
    
    # Create realistic labels based on features
    risk_scores = (
        0.3 * (X_train[:, 0] > 20).astype(float) +  # Late night
        0.2 * (X_train[:, 1] == 5).astype(float) +  # Friday
        0.4 * (X_train[:, 9] > 0.7).astype(float) + # High traffic
        0.3 * (X_train[:, 14] > 2).astype(float) +  # Bad weather
        0.2 * (X_train[:, 5] > 20).astype(float) +  # High wind
        np.random.normal(0, 0.1, n_samples)
    )
    
    y_risk = np.clip((risk_scores * 3).astype(int), 0, 3)  # 0-3 risk levels
    y_severity = np.clip((risk_scores * 2.5 + np.random.normal(0, 0.5, n_samples)).astype(int), 0, 3)  # 0-3 severity levels
    
    # Create and train risk model
    logger.info("Creating risk prediction model...")
    risk_model = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    risk_model.fit(X_train, y_risk)
    
    # Create and train severity model
    logger.info("Creating severity prediction model...")
    severity_model = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    severity_model.fit(X_train, y_severity)
    
    # Save models
    logger.info("Saving models...")
    with open('models/risk_model.pkl', 'wb') as f:
        pickle.dump(risk_model, f)
    
    with open('models/severity_model.pkl', 'wb') as f:
        pickle.dump(severity_model, f)
    
    with open('models/feature_info.pkl', 'wb') as f:
        pickle.dump(feature_info, f)
    
    logger.info("✅ Models created and saved successfully!")
    
    # Test the models
    logger.info("Testing models...")
    test_sample = np.random.randn(1, 16)
    test_sample[0, 0] = 12  # hour
    test_sample[0, 1] = 2   # day_of_week
    test_sample[0, 2] = 6   # month
    test_sample[0, 3] = 25  # temperature
    test_sample[0, 4] = 60  # humidity
    test_sample[0, 5] = 10  # wind_speed
    test_sample[0, 6] = 10  # visibility
    test_sample[0, 7] = 0   # precipitation
    test_sample[0, 8] = 1013 # pressure
    test_sample[0, 9] = 0.5 # traffic_density
    test_sample[0, 10] = 0  # road_type_highway
    test_sample[0, 11] = 1  # road_type_arterial
    test_sample[0, 12] = 0  # road_type_collector
    test_sample[0, 13] = 0  # road_type_local
    test_sample[0, 14] = 0  # weather_condition_numeric
    test_sample[0, 15] = 1000 # population_density
    
    risk_pred = risk_model.predict(test_sample)
    severity_pred = severity_model.predict(test_sample)
    
    logger.info(f"✅ Test prediction - Risk: {risk_pred[0]}, Severity: {severity_pred[0]}")
    
    return True

if __name__ == "__main__":
    create_working_models()