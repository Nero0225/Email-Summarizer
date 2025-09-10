"""
User model for Email Summarizer application

This module contains the User model and related enums for user management.
"""
import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum
from app import db


class UserStatus(enum.Enum):
    """User account status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class UserRole(enum.Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"


class User(UserMixin, db.Model):
    """
    User model for authentication and authorization
    
    Attributes:
        id: Primary key
        username: Unique username for login
        email: User's email address
        full_name: User's full name
        password_hash: Hashed password
        status: Account status (pending, approved, etc.)
        role: User role (user, admin)
        microsoft_account_email: Linked Microsoft 365 email
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last login timestamp
        approved_at: Approval timestamp
        approved_by_id: ID of admin who approved
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Status and role
    status = db.Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    role = db.Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # Microsoft integration
    microsoft_account_email = db.Column(db.String(128), index=True)
    microsoft_account_linked_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.relationship('User', remote_side=[id], backref='approved_users')
    
    # One-to-many relationships
    digest_records = db.relationship('DigestRecord', back_populates='user', 
                                   cascade='all, delete-orphan')
    microsoft_tokens = db.relationship('MicrosoftToken', back_populates='user',
                                     cascade='all, delete-orphan', uselist=False)
    settings = db.relationship('UserSettings', back_populates='user',
                             cascade='all, delete-orphan', uselist=False)
    daily_usage = db.relationship('DailyUsage', back_populates='user',
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """
        Set user password (hashed)
        
        Args:
            password (str): Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Check if provided password matches
        
        Args:
            password (str): Plain text password to check
            
        Returns:
            bool: True if password matches, False otherwise
        """
        # OAuth users may not have a password
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_approved(self):
        """Check if user account is approved"""
        return self.status == UserStatus.APPROVED
    
    @property
    def is_active(self):
        """Check if user account is active (required by Flask-Login)"""
        return self.status == UserStatus.APPROVED
    
    @property
    def has_microsoft_linked(self):
        """Check if user has linked Microsoft account"""
        return bool(self.microsoft_account_email)
    
    @property
    def is_oauth_user(self):
        """Check if user registered via OAuth (no password)"""
        return self.password_hash is None and self.microsoft_account_email is not None
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def approve(self, admin_user):
        """
        Approve user account
        
        Args:
            admin_user (User): Admin user approving the account
        """
        self.status = UserStatus.APPROVED
        self.approved_at = datetime.utcnow()
        self.approved_by = admin_user
        db.session.commit()
    
    def reject(self, admin_user):
        """
        Reject user account
        
        Args:
            admin_user (User): Admin user rejecting the account
        """
        self.status = UserStatus.REJECTED
        self.approved_at = datetime.utcnow()
        self.approved_by = admin_user
        db.session.commit()
    
    def suspend(self):
        """Suspend user account"""
        self.status = UserStatus.SUSPENDED
        db.session.commit()
    
    def link_microsoft_account(self, microsoft_email):
        """
        Link Microsoft 365 account
        
        Args:
            microsoft_email (str): Microsoft account email address
        """
        self.microsoft_account_email = microsoft_email
        self.microsoft_account_linked_at = datetime.utcnow()
        db.session.commit()
    
    def unlink_microsoft_account(self):
        """Unlink Microsoft 365 account"""
        self.microsoft_account_email = None
        self.microsoft_account_linked_at = None
        # Also remove tokens
        if self.microsoft_tokens:
            db.session.delete(self.microsoft_tokens)
        db.session.commit()
    
    def to_dict(self):
        """
        Convert user to dictionary representation
        
        Returns:
            dict: User data dictionary
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'status': self.status.value,
            'role': self.role.value,
            'microsoft_linked': self.has_microsoft_linked,
            'microsoft_email': self.microsoft_account_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }
