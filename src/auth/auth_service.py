"""
SafeRoute Navigator - Authentication Service
Handles user authentication, sessions, and authorization
"""

from flask import session, request, g
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import secrets
import logging

from src.models.user import User, user_db

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for user management"""
    
    def __init__(self):
        self.session_timeout = timedelta(hours=24)  # 24 hour sessions
        self._initialize_demo_users()
    
    def _initialize_demo_users(self):
        """Initialize demo users if they don't exist"""
        try:
            # Create demo admin user
            if not user_db.get_user_by_email('admin@saferoute.com'):
                admin_user = user_db.create_user(
                    email='admin@saferoute.com',
                    username='admin',
                    password='admin123',  # Demo password
                    full_name='Admin User',
                    role='admin'
                )
                admin_user.is_verified = True
                user_db.update_user(admin_user)
                logger.info("Created demo admin user: admin@saferoute.com / admin123")
            
            # Create demo regular user
            if not user_db.get_user_by_email('user@saferoute.com'):
                demo_user = user_db.create_user(
                    email='user@saferoute.com',
                    username='demouser',
                    password='user123',  # Demo password
                    full_name='Demo User',
                    role='user'
                )
                demo_user.is_verified = True
                user_db.update_user(demo_user)
                logger.info("Created demo regular user: user@saferoute.com / user123")
        
        except Exception as e:
            logger.error(f"Error initializing demo users: {e}")
    
    def login(self, email_or_username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate user login
        Returns: (success, message, user)
        """
        try:
            # Try to find user by email or username
            user = user_db.get_user_by_email(email_or_username)
            if not user:
                user = user_db.get_user_by_username(email_or_username)
            
            if not user:
                return False, "User not found", None
            
            if not user.is_active:
                return False, "Account is deactivated", None
            
            if not user.verify_password(password):
                return False, "Invalid password", None
            
            # Update last login
            user.last_login = datetime.utcnow()
            user_db.update_user(user)
            
            # Create session
            self._create_session(user)
            
            logger.info(f"User {user.username} logged in successfully")
            return True, "Login successful", user
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, "Login failed", None
    
    def register(self, email: str, username: str, password: str, full_name: str) -> Tuple[bool, str, Optional[User]]:
        """
        Register new user
        Returns: (success, message, user)
        """
        try:
            # Validate inputs
            if len(password) < 6:
                return False, "Password must be at least 6 characters", None
            
            if '@' not in email or '.' not in email:
                return False, "Invalid email format", None
            
            if len(username) < 3:
                return False, "Username must be at least 3 characters", None
            
            # Create user
            user = user_db.create_user(
                email=email,
                username=username,
                password=password,
                full_name=full_name,
                role='user'
            )
            
            logger.info(f"New user registered: {user.username}")
            return True, "Registration successful", user
            
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, "Registration failed", None
    
    def logout(self) -> bool:
        """Logout current user"""
        try:
            user_id = session.get('user_id')
            if user_id:
                user = user_db.get_user_by_id(user_id)
                if user:
                    logger.info(f"User {user.username} logged out")
            
            session.clear()
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return None
            
            # Check session timeout
            login_time = session.get('login_time')
            if login_time:
                login_datetime = datetime.fromisoformat(login_time)
                if datetime.utcnow() - login_datetime > self.session_timeout:
                    session.clear()
                    return None
            
            user = user_db.get_user_by_id(user_id)
            if user and user.is_active:
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            return None
    
    def require_auth(self, required_role: Optional[str] = None):
        """Decorator to require authentication"""
        def decorator(f):
            def wrapper(*args, **kwargs):
                user = self.get_current_user()
                if not user:
                    return {'status': 'error', 'message': 'Authentication required'}, 401
                
                if required_role and user.role != required_role and user.role != 'admin':
                    return {'status': 'error', 'message': 'Insufficient permissions'}, 403
                
                g.current_user = user
                return f(*args, **kwargs)
            
            wrapper.__name__ = f.__name__
            return wrapper
        return decorator
    
    def _create_session(self, user: User):
        """Create user session"""
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['login_time'] = datetime.utcnow().isoformat()
        session.permanent = True
        session.modified = True
    
    def update_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Update user preferences"""
        try:
            user = user_db.get_user_by_id(user_id)
            if not user:
                return False
            
            user.preferences.update(preferences)
            return user_db.update_user(user)
            
        except Exception as e:
            logger.error(f"Update preferences error: {e}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            user = user_db.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            if not user.verify_password(old_password):
                return False, "Current password is incorrect"
            
            if len(new_password) < 6:
                return False, "New password must be at least 6 characters"
            
            user.password_hash = User.hash_password(new_password)
            user_db.update_user(user)
            
            logger.info(f"Password changed for user {user.username}")
            return True, "Password changed successfully"
            
        except Exception as e:
            logger.error(f"Change password error: {e}")
            return False, "Password change failed"
    
    def get_user_stats(self) -> Dict:
        """Get user statistics (admin only)"""
        try:
            stats = user_db.get_user_count()
            
            # Add additional stats
            users = user_db.get_all_users()
            recent_users = [u for u in users if u.created_at and 
                           (datetime.utcnow() - u.created_at).days <= 7]
            
            stats['recent_registrations'] = len(recent_users)
            stats['recent_logins'] = sum(1 for u in users if u.last_login and 
                                       (datetime.utcnow() - u.last_login).hours <= 24)
            
            return stats
            
        except Exception as e:
            logger.error(f"Get user stats error: {e}")
            return {}

# Global auth service instance
auth_service = AuthService()