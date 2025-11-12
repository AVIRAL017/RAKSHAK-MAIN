#!/usr/bin/env python3
"""
SafeRoute Navigator v2.0
A comprehensive road safety navigation system with AI-powered risk prediction.

Features:
- Real-time route optimization with safety scoring
- Dynamic hotspot detection and avoidance
- Weather-aware risk assessment
- ML-powered incident prediction
- Zero external API dependencies (demo data only)
"""

import os
import sys
import logging
from flask import Flask, render_template, jsonify, redirect, url_for, g, request
from flask_cors import CORS
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'saferoute-navigator-v2-secure-key-2024'
    app.config['DEBUG'] = True
    app.config['ENV'] = 'development'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 24 hour sessions
    # Session cookie hardening (dev-safe defaults)
    app.config['SESSION_COOKIE_NAME'] = 'raks_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False  # set True behind HTTPS
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_PATH'] = '/'
    # Enable CORS for API endpoints (allow credentials for session cookies)
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5000", "http://127.0.0.1:5000"]}},
        supports_credentials=True
    )
    
    # Lazy import auth service to avoid circulars
    try:
        from src.auth.auth_service import auth_service
    except Exception as _e:
        auth_service = None
        logger.warning(f"Auth service unavailable during init: {_e}")
    
    # Global user context and simple route protection for templates
    @app.before_request
    def load_current_user():
        g.current_user = None
        if auth_service:
            try:
                g.current_user = auth_service.get_current_user()
            except Exception as e:
                logger.debug(f"get_current_user failed: {e}")
    
    def require_login():
        if not getattr(g, 'current_user', None):
            # redirect to login with next parameter
            next_url = request.path
            return redirect(url_for('login_page', next=next_url))
        return None
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    # Main routes
    @app.route('/')
    def index():
        """Landing page."""
        return render_template('home.html')
    
    @app.route('/map')
    def map_view():
        """Interactive map interface."""
        return render_template('map.html')
    
    @app.route('/analytics')
    def analytics():
        """Risk analytics dashboard."""
        # Optional: require auth to access analytics
        check = require_login()
        if check: return check
        return render_template('analytics.html')
    
    @app.route('/about')
    def about():
        """About page."""
        return render_template('about.html')
    
    @app.route('/login')
    def login_page():
        """Login page."""
        return render_template('login.html')
    
    @app.route('/signup')
    def signup_page():
        """Signup page."""
        return render_template('signup.html')
    
    @app.route('/dashboard')
    def dashboard():
        """User dashboard."""
        check = require_login()
        if check: return check
        return render_template('dashboard.html')
    
    @app.route('/admin')
    def admin_panel():
        """Admin panel."""
        check = require_login()
        if check: return check
        if not getattr(g, 'current_user', None) or g.current_user.role not in ('admin',):
            return redirect(url_for('dashboard'))
        return render_template('admin.html')
    
    @app.route('/settings')
    def settings():
        """User settings page."""
        check = require_login()
        if check: return check
        return render_template('settings.html')
    
    @app.route('/profile')
    def profile():
        """User profile page."""
        check = require_login()
        if check: return check
        return render_template('profile.html')
    
    @app.route('/help')
    def help_page():
        """Help and support page."""
        return render_template('help.html')
    
    @app.route('/emergency-command')
    def emergency_command():
        """Emergency Command Center for dispatch operations."""
        check = require_login()
        if check: return check
        return render_template('emergency-command.html')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """System health check."""
        return jsonify({
            'status': 'healthy',
            'version': '2.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'route_service': 'operational',
                'hotspot_service': 'operational', 
                'weather_service': 'operational',
                'ml_service': 'operational'
            }
        })
    
    # Register API blueprints
    try:
        from src.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("✅ API routes registered successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to register API routes: {e}")
    
    return app

if __name__ == '__main__':
    # Create application
    app = create_app()
    
    # Startup information
    print("🚀 SafeRoute Navigator v2.0")
    print("=" * 50)
    print(f"Environment: {app.config['ENV']}")
    print(f"Debug mode: {app.config['DEBUG']}")
    print("Features: AI Risk Prediction, Real-time Hotspots, Weather Integration")
    print("Data Source: Demo Data (No External API Dependencies)")
    print("=" * 50)
    
    # Start the application
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 SafeRoute Navigator shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        sys.exit(1)
