#!/usr/bin/env python3
"""
SafeRoute Navigator Database API Routes
Integration layer between Flask API and database models.
"""

from flask import Blueprint, jsonify, request, session
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

# Import database models
try:
    from src.database.models import db_manager, user_model, route_model, statistics_model
except ImportError:
    # Fallback for testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from database.models import db_manager, user_model, route_model, statistics_model

logger = logging.getLogger(__name__)

# Create blueprint for database routes
db_api = Blueprint('database_api', __name__)

# ==========================================
# User Management Routes
# ==========================================

@db_api.route('/users', methods=['POST'])
def create_user():
    """Create a new user account."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if user already exists
        existing_user = user_model.get_user_by_username(data['username'])
        if existing_user:
            return jsonify({
                'status': 'error',
                'message': 'Username already exists'
            }), 409
        
        existing_email = user_model.get_user_by_email(data['email'])
        if existing_email:
            return jsonify({
                'status': 'error',
                'message': 'Email already registered'
            }), 409
        
        # Create user (in real app, hash password properly)
        user_id = user_model.create_user(
            username=data['username'],
            email=data['email'],
            password_hash=f"hashed_{data['password']}",  # In real app, use proper hashing
            full_name=data['full_name'],
            phone=data.get('phone')
        )
        
        if user_id:
            return jsonify({
                'status': 'success',
                'message': 'User created successfully',
                'user_id': user_id
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create user'
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@db_api.route('/users/<username>', methods=['GET'])
def get_user(username):
    """Get user information by username."""
    try:
        user = user_model.get_user_by_username(username)
        if user:
            # Remove sensitive information
            safe_user = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'phone': user['phone'],
                'created_at': user['created_at'],
                'last_login': user['last_login'],
                'is_admin': user['is_admin'],
                'verification_status': user['verification_status']
            }
            return jsonify({
                'status': 'success',
                'user': safe_user
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@db_api.route('/auth/login', methods=['POST'])
def login_user():
    """Authenticate user login."""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'status': 'error',
                'message': 'Username and password required'
            }), 400
        
        user = user_model.get_user_by_username(username)
        if user and user['password_hash'] == f"hashed_{password}":  # In real app, verify proper hash
            # Update last login
            user_model.update_last_login(user['id'])
            
            # Set session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'is_admin': user['is_admin']
                }
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid username or password'
            }), 401
            
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@db_api.route('/auth/logout', methods=['POST'])
def logout_user():
    """Logout current user."""
    try:
        session.clear()
        return jsonify({
            'status': 'success',
            'message': 'Logout successful'
        }), 200
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@db_api.route('/auth/user', methods=['GET'])
def get_current_user():
    """Get current authenticated user."""
    try:
        if 'user_id' not in session:
            return jsonify({
                'status': 'error',
                'message': 'Not authenticated'
            }), 401
        
        user = user_model.get_user_by_username(session['username'])
        if user:
            return jsonify({
                'status': 'success',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'is_admin': user['is_admin'],
                    'last_login': user['last_login']
                }
            }), 200
        else:
            session.clear()
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

# ==========================================
# Route Management Routes
# ==========================================

@db_api.route('/routes', methods=['POST'])
def save_route():
    """Save a calculated route."""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        # Validate required route data
        required_fields = ['start_lat', 'start_lng', 'end_lat', 'end_lng']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        route_id = route_model.save_route(user_id, data)
        
        if route_id:
            # Update statistics
            statistics_model.update_statistic('system', 'total_routes', 
                                            statistics_model.get_statistics('system')[0].get('stat_value', 0) + 1)
            
            return jsonify({
                'status': 'success',
                'message': 'Route saved successfully',
                'route_id': route_id
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save route'
            }), 500
            
    except Exception as e:
        logger.error(f"Error saving route: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@db_api.route('/routes/user/<int:user_id>', methods=['GET'])
def get_user_routes(user_id):
    """Get routes for a specific user."""
    try:
        # Check if requesting own routes or admin access
        current_user_id = session.get('user_id')
        is_admin = session.get('is_admin', False)
        
        if not current_user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        if current_user_id != user_id and not is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Access denied'
            }), 403
        
        limit = request.args.get('limit', 50, type=int)
        routes = route_model.get_user_routes(user_id, limit)
        
        return jsonify({
            'status': 'success',
            'routes': routes,
            'count': len(routes)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user routes: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@db_api.route('/routes/my', methods=['GET'])
def get_my_routes():
    """Get routes for current user."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        limit = request.args.get('limit', 50, type=int)
        routes = route_model.get_user_routes(user_id, limit)
        
        return jsonify({
            'status': 'success',
            'routes': routes,
            'count': len(routes)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting my routes: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

# ==========================================
# Statistics and Analytics Routes
# ==========================================

@db_api.route('/stats/overview', methods=['GET'])
def get_stats_overview():
    """Get system statistics overview."""
    try:
        days = request.args.get('days', 30, type=int)
        stats = statistics_model.get_statistics(days=days)
        
        # Group statistics by type
        grouped_stats = {}
        for stat in stats:
            stat_type = stat['stat_type']
            if stat_type not in grouped_stats:
                grouped_stats[stat_type] = {}
            grouped_stats[stat_type][stat['stat_key']] = {
                'value': stat['stat_value'],
                'data': stat['stat_data'],
                'date': stat['date']
            }
        
        return jsonify({
            'status': 'success',
            'statistics': grouped_stats,
            'period_days': days
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats overview: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@db_api.route('/stats/update', methods=['POST'])
def update_statistic():
    """Update a system statistic (admin only)."""
    try:
        if not session.get('is_admin', False):
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        data = request.get_json()
        stat_type = data.get('stat_type')
        stat_key = data.get('stat_key')
        value = data.get('value')
        
        if not all([stat_type, stat_key, value is not None]):
            return jsonify({
                'status': 'error',
                'message': 'stat_type, stat_key, and value are required'
            }), 400
        
        statistics_model.update_statistic(
            stat_type, 
            stat_key, 
            float(value), 
            data.get('data')
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Statistic updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating statistic: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

# ==========================================
# Hotspots and Incidents Routes
# ==========================================

@db_api.route('/hotspots', methods=['GET'])
def get_hotspots():
    """Get active hotspots."""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM hotspots 
                WHERE active = 1 
                ORDER BY severity DESC, created_at DESC
            """)
            hotspots = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'status': 'success',
            'hotspots': hotspots,
            'count': len(hotspots)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting hotspots: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@db_api.route('/incidents', methods=['POST'])
def report_incident():
    """Report a new safety incident."""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Validate required fields
        required_fields = ['lat', 'lng', 'incident_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO incidents (user_id, lat, lng, incident_type, severity, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                data['lat'],
                data['lng'],
                data['incident_type'],
                data.get('severity', 'medium'),
                data.get('description')
            ))
            incident_id = cursor.lastrowid
        
        return jsonify({
            'status': 'success',
            'message': 'Incident reported successfully',
            'incident_id': incident_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error reporting incident: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

# ==========================================
# Database Health and Diagnostics
# ==========================================

@db_api.route('/health', methods=['GET'])
def database_health():
    """Check database health and connection."""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1")
            
            # Get table counts
            tables = ['users', 'routes', 'hotspots', 'statistics', 'incidents']
            table_counts = {}
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
        
        return jsonify({
            'status': 'healthy',
            'database_path': db_manager.db_path,
            'table_counts': table_counts,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == "__main__":
    # Test the database routes
    from flask import Flask
    
    app = Flask(__name__)
    app.secret_key = 'test_secret_key'
    app.register_blueprint(db_api, url_prefix='/db-api')
    
    print("🔄 Testing database API routes...")
    
    with app.test_client() as client:
        # Test health check
        response = client.get('/db-api/health')
        print(f"Health check: {response.status_code} - {response.json}")
        
        # Test user creation
        user_data = {
            'username': 'test_api_user',
            'email': 'testapi@example.com',
            'password': 'testpass',
            'full_name': 'Test API User'
        }
        response = client.post('/db-api/users', json=user_data)
        print(f"User creation: {response.status_code} - {response.json}")
    
    print("✅ Database API routes test completed!")