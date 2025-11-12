#!/usr/bin/env python3
"""
SafeRoute Navigator Database Models
Comprehensive database schema for user management, route history, and statistics tracking.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import logging
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Central database management class for SafeRoute Navigator."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to application root directory
            app_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(app_root, 'data', 'saferoute.db')
        
        self.db_path = db_path
        self.ensure_data_directory()
        self.initialize_database()
    
    def ensure_data_directory(self):
        """Ensure the data directory exists."""
        data_dir = os.path.dirname(self.db_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def initialize_database(self):
        """Initialize database with all required tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create tables
                self._create_users_table(cursor)
                self._create_routes_table(cursor)
                self._create_hotspots_table(cursor)
                self._create_user_preferences_table(cursor)
                self._create_route_history_table(cursor)
                self._create_statistics_table(cursor)
                self._create_incidents_table(cursor)
                self._create_feedback_table(cursor)
                
                # Insert default data
                self._insert_default_data(cursor)
                
                logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _create_users_table(self, cursor):
        """Create users table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                profile_picture TEXT,
                verification_status VARCHAR(20) DEFAULT 'pending'
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)")
    
    def _create_routes_table(self, cursor):
        """Create routes table for calculated routes."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                start_lat REAL NOT NULL,
                start_lng REAL NOT NULL,
                end_lat REAL NOT NULL,
                end_lng REAL NOT NULL,
                start_address TEXT,
                end_address TEXT,
                route_type VARCHAR(20) DEFAULT 'balanced',
                distance_km REAL,
                duration_minutes INTEGER,
                safety_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                route_data TEXT,
                weather_conditions TEXT,
                traffic_conditions TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_routes_user_id ON routes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_routes_created_at ON routes(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_routes_type ON routes(route_type)")
    
    def _create_hotspots_table(self, cursor):
        """Create hotspots table for danger zones."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotspots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                radius_meters INTEGER DEFAULT 500,
                risk_level VARCHAR(20) DEFAULT 'medium',
                incident_type VARCHAR(50),
                description TEXT,
                severity REAL DEFAULT 5.0,
                reported_by INTEGER,
                verified BOOLEAN DEFAULT 0,
                active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                incident_count INTEGER DEFAULT 1,
                last_incident DATETIME,
                FOREIGN KEY (reported_by) REFERENCES users (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotspots_location ON hotspots(lat, lng)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotspots_risk_level ON hotspots(risk_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotspots_active ON hotspots(active)")
    
    def _create_user_preferences_table(self, cursor):
        """Create user preferences table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                preferred_route_type VARCHAR(20) DEFAULT 'balanced',
                avoid_toll_roads BOOLEAN DEFAULT 0,
                avoid_highways BOOLEAN DEFAULT 0,
                safety_priority REAL DEFAULT 7.0,
                speed_priority REAL DEFAULT 5.0,
                notifications_enabled BOOLEAN DEFAULT 1,
                location_sharing BOOLEAN DEFAULT 1,
                dark_mode BOOLEAN DEFAULT 0,
                language VARCHAR(10) DEFAULT 'en',
                units VARCHAR(10) DEFAULT 'metric',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_prefs_user_id ON user_preferences(user_id)")
    
    def _create_route_history_table(self, cursor):
        """Create route history table for tracking user journeys."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS route_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                route_id INTEGER,
                start_time DATETIME,
                end_time DATETIME,
                actual_duration_minutes INTEGER,
                distance_traveled_km REAL,
                safety_incidents INTEGER DEFAULT 0,
                completion_status VARCHAR(20) DEFAULT 'completed',
                feedback_rating INTEGER,
                feedback_text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (route_id) REFERENCES routes (id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_route_history_user_id ON route_history(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_route_history_start_time ON route_history(start_time)")
    
    def _create_statistics_table(self, cursor):
        """Create statistics table for system analytics."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type VARCHAR(50) NOT NULL,
                stat_key VARCHAR(100) NOT NULL,
                stat_value REAL,
                stat_data TEXT,
                date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stat_type, stat_key, date)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statistics_type_date ON statistics(stat_type, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statistics_key ON statistics(stat_key)")
    
    def _create_incidents_table(self, cursor):
        """Create incidents table for reported safety issues."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                incident_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) DEFAULT 'medium',
                description TEXT,
                image_url TEXT,
                status VARCHAR(20) DEFAULT 'reported',
                verified BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                resolution_notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(lat, lng)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
    
    def _create_feedback_table(self, cursor):
        """Create feedback table for user feedback and support."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback_type VARCHAR(50) DEFAULT 'general',
                subject VARCHAR(200),
                message TEXT NOT NULL,
                rating INTEGER,
                status VARCHAR(20) DEFAULT 'open',
                priority VARCHAR(20) DEFAULT 'medium',
                assigned_to INTEGER,
                response TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)")
    
    def _insert_default_data(self, cursor):
        """Insert default data for testing and demo purposes."""
        try:
            # Insert demo user
            cursor.execute("""
                INSERT OR IGNORE INTO users 
                (username, email, password_hash, full_name, is_active, is_admin) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('demo_user', 'demo@saferoute.com', 'demo_hash', 'Demo User', 1, 0))
            
            # Insert admin user
            cursor.execute("""
                INSERT OR IGNORE INTO users 
                (username, email, password_hash, full_name, is_active, is_admin) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('admin', 'admin@saferoute.com', 'admin_hash', 'System Admin', 1, 1))
            
            # Insert sample hotspots (Delhi area)
            sample_hotspots = [
                ('Yamuna Expressway Junction', 28.6139, 77.2090, 800, 'high', 'accident_prone', 'High accident rate during peak hours', 8.5),
                ('CP Metro Station Area', 28.6315, 77.2167, 300, 'medium', 'theft', 'Crowded area with pickpocket incidents', 6.0),
                ('Red Light Area - GB Road', 28.6563, 77.2194, 500, 'very_high', 'crime', 'High crime rate area', 9.2),
                ('Lajpat Nagar Market', 28.5651, 77.2432, 200, 'low', 'traffic', 'Heavy traffic congestion', 3.5),
                ('Karol Bagh Market', 28.6517, 77.1910, 400, 'medium', 'theft', 'Busy market area', 5.8)
            ]
            
            for hotspot in sample_hotspots:
                cursor.execute("""
                    INSERT OR IGNORE INTO hotspots 
                    (name, lat, lng, radius_meters, risk_level, incident_type, description, severity, active) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, hotspot)
            
            # Insert sample statistics
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            sample_stats = [
                ('system', 'total_routes', 15420, None, today),
                ('system', 'active_users', 8950, None, today),
                ('system', 'active_hotspots', 34, None, today),
                ('safety', 'avg_safety_score', 8.2, None, today),
                ('system', 'total_routes', 15300, None, yesterday),
                ('system', 'active_users', 8750, None, yesterday),
            ]
            
            for stat in sample_stats:
                cursor.execute("""
                    INSERT OR REPLACE INTO statistics 
                    (stat_type, stat_key, stat_value, stat_data, date) 
                    VALUES (?, ?, ?, ?, ?)
                """, stat)
            
            logger.info("✅ Default data inserted successfully")
            
        except Exception as e:
            logger.error(f"Error inserting default data: {e}")


class UserModel:
    """User model for authentication and profile management."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_user(self, username: str, email: str, password_hash: str, full_name: str, **kwargs) -> Optional[int]:
        """Create a new user."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, full_name, phone, profile_picture)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, email, password_hash, full_name, 
                      kwargs.get('phone'), kwargs.get('profile_picture')))
                
                user_id = cursor.lastrowid
                
                # Create default preferences for new user
                self._create_default_preferences(cursor, user_id)
                
                return user_id
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            return False
    
    def _create_default_preferences(self, cursor, user_id: int):
        """Create default preferences for a new user."""
        cursor.execute("""
            INSERT INTO user_preferences (user_id, preferred_route_type, safety_priority, speed_priority)
            VALUES (?, 'balanced', 7.0, 5.0)
        """, (user_id,))


class RouteModel:
    """Route model for managing calculated routes and history."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_route(self, user_id: int, route_data: Dict) -> Optional[int]:
        """Save a calculated route."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO routes 
                    (user_id, start_lat, start_lng, end_lat, end_lng, start_address, end_address,
                     route_type, distance_km, duration_minutes, safety_score, route_data, 
                     weather_conditions, traffic_conditions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    route_data.get('start_lat'),
                    route_data.get('start_lng'),
                    route_data.get('end_lat'),
                    route_data.get('end_lng'),
                    route_data.get('start_address'),
                    route_data.get('end_address'),
                    route_data.get('route_type', 'balanced'),
                    route_data.get('distance_km'),
                    route_data.get('duration_minutes'),
                    route_data.get('safety_score'),
                    json.dumps(route_data.get('route_geometry', {})),
                    json.dumps(route_data.get('weather_conditions', {})),
                    json.dumps(route_data.get('traffic_conditions', {}))
                ))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving route: {e}")
            return None
    
    def get_user_routes(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's recent routes."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM routes WHERE user_id = ? 
                    ORDER BY created_at DESC LIMIT ?
                """, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user routes: {e}")
            return []


class StatisticsModel:
    """Statistics model for analytics and reporting."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def update_statistic(self, stat_type: str, stat_key: str, value: float, data: Dict = None, date: datetime = None):
        """Update or create a statistic entry."""
        if date is None:
            date = datetime.now().date()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO statistics 
                    (stat_type, stat_key, stat_value, stat_data, date)
                    VALUES (?, ?, ?, ?, ?)
                """, (stat_type, stat_key, value, json.dumps(data) if data else None, date))
        except Exception as e:
            logger.error(f"Error updating statistic: {e}")
    
    def get_statistics(self, stat_type: str = None, days: int = 30) -> List[Dict]:
        """Get statistics for a given period."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                start_date = datetime.now().date() - timedelta(days=days)
                
                if stat_type:
                    cursor.execute("""
                        SELECT * FROM statistics 
                        WHERE stat_type = ? AND date >= ? 
                        ORDER BY date DESC, stat_key
                    """, (stat_type, start_date))
                else:
                    cursor.execute("""
                        SELECT * FROM statistics 
                        WHERE date >= ? 
                        ORDER BY date DESC, stat_type, stat_key
                    """, (start_date,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return []


# Initialize database manager instance
db_manager = DatabaseManager()

# Model instances for easy access
user_model = UserModel(db_manager)
route_model = RouteModel(db_manager)
statistics_model = StatisticsModel(db_manager)

if __name__ == "__main__":
    # Test database initialization
    try:
        print("🔄 Testing database initialization...")
        db_manager.initialize_database()
        print("✅ Database test completed successfully!")
        
        # Test user creation
        print("🔄 Testing user operations...")
        user_id = user_model.create_user(
            username="test_user",
            email="test@example.com",
            password_hash="test_hash",
            full_name="Test User"
        )
        print(f"✅ Test user created with ID: {user_id}")
        
        # Test statistics
        print("🔄 Testing statistics...")
        statistics_model.update_statistic('test', 'sample_metric', 42.0)
        stats = statistics_model.get_statistics('test')
        print(f"✅ Statistics test completed: {len(stats)} records found")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")