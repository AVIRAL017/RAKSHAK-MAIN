"""
SafeRoute Navigator - User Models
Database models for user management and authentication
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
import hashlib
import secrets
import json
import os

@dataclass
class User:
    """User model for authentication and profile management"""
    
    id: str
    email: str
    username: str
    password_hash: str
    full_name: str
    role: str = 'user'  # 'user', 'admin', 'premium'
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = None
    last_login: datetime = None
    preferences: Dict = None
    profile_picture: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.preferences is None:
            self.preferences = self._default_preferences()
    
    @staticmethod
    def _default_preferences():
        """Default user preferences"""
        return {
            'route_type': 'balanced',
            'vehicle_type': 'car',
            'avoid_tolls': False,
            'avoid_highways': False,
            'risk_tolerance': 'medium',
            'notifications': {
                'weather_alerts': True,
                'traffic_updates': True,
                'safety_warnings': True,
                'route_suggestions': True
            },
            'privacy': {
                'share_location': False,
                'anonymous_analytics': True,
                'data_retention': '1year'
            }
        }
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = self.password_hash.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        except Exception:
            return False
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferences': self.preferences,
            'profile_picture': self.profile_picture
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary"""
        # Convert datetime strings back to datetime objects
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        last_login = None
        if data.get('last_login'):
            last_login = datetime.fromisoformat(data['last_login'])
        
        return cls(
            id=data['id'],
            email=data['email'],
            username=data['username'],
            password_hash=data['password_hash'],
            full_name=data['full_name'],
            role=data.get('role', 'user'),
            is_active=data.get('is_active', True),
            is_verified=data.get('is_verified', False),
            created_at=created_at,
            last_login=last_login,
            preferences=data.get('preferences'),
            profile_picture=data.get('profile_picture')
        )


class UserDatabase:
    """Simple file-based user database for demo purposes"""
    
    def __init__(self, db_path: str = 'users.json'):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure database file exists"""
        if not os.path.exists(self.db_path):
            self._save_users({})
    
    def _load_users(self) -> Dict[str, Dict]:
        """Load users from file"""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_users(self, users: Dict[str, Dict]):
        """Save users to file"""
        with open(self.db_path, 'w') as f:
            json.dump(users, f, indent=2)
    
    def create_user(self, email: str, username: str, password: str, full_name: str, role: str = 'user') -> User:
        """Create a new user"""
        users = self._load_users()
        
        # Check if email or username already exists
        for user_data in users.values():
            if user_data['email'] == email:
                raise ValueError("Email already exists")
            if user_data['username'] == username:
                raise ValueError("Username already exists")
        
        # Generate user ID
        user_id = secrets.token_urlsafe(16)
        
        # Create user object
        user = User(
            id=user_id,
            email=email,
            username=username,
            password_hash=User.hash_password(password),
            full_name=full_name,
            role=role,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        user_dict = user.to_dict()
        user_dict['password_hash'] = user.password_hash  # Include password hash in storage
        users[user_id] = user_dict
        self._save_users(users)
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        users = self._load_users()
        user_data = users.get(user_id)
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = self._load_users()
        for user_data in users.values():
            if user_data['email'] == email:
                return User.from_dict(user_data)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        users = self._load_users()
        for user_data in users.values():
            if user_data['username'] == username:
                return User.from_dict(user_data)
        return None
    
    def update_user(self, user: User) -> bool:
        """Update user in database"""
        users = self._load_users()
        if user.id in users:
            user_dict = user.to_dict()
            user_dict['password_hash'] = user.password_hash
            users[user.id] = user_dict
            self._save_users(users)
            return True
        return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user from database"""
        users = self._load_users()
        if user_id in users:
            del users[user_id]
            self._save_users(users)
            return True
        return False
    
    def get_all_users(self, role_filter: Optional[str] = None) -> List[User]:
        """Get all users, optionally filtered by role"""
        users = self._load_users()
        user_objects = [User.from_dict(data) for data in users.values()]
        
        if role_filter:
            user_objects = [u for u in user_objects if u.role == role_filter]
        
        return sorted(user_objects, key=lambda x: x.created_at, reverse=True)
    
    def get_user_count(self) -> Dict[str, int]:
        """Get user count statistics"""
        users = self._load_users()
        total = len(users)
        active = sum(1 for u in users.values() if u.get('is_active', True))
        verified = sum(1 for u in users.values() if u.get('is_verified', False))
        
        role_counts = {}
        for user_data in users.values():
            role = user_data.get('role', 'user')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            'total': total,
            'active': active,
            'verified': verified,
            'roles': role_counts
        }

# Global user database instance
user_db = UserDatabase()