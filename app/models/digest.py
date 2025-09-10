"""
Digest-related models for Email Summarizer application

This module contains models for digest records, Microsoft tokens,
user settings, and daily usage tracking.
"""
from datetime import datetime
import json
from app import db


class DigestRecord(db.Model):
    """
    Model for tracking digest generation history
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        generated_at: Generation timestamp
        email_count: Number of emails processed
        meeting_count: Number of meetings included
        digest_data: JSON blob of digest content
        data_source: Source of data (office365, test_data)
        processing_time: Time taken to generate (seconds)
        error_message: Error message if generation failed
    """
    __tablename__ = 'digest_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Digest metadata
    email_count = db.Column(db.Integer, default=0)
    meeting_count = db.Column(db.Integer, default=0)
    digest_data = db.Column(db.JSON)
    data_source = db.Column(db.String(32), default='office365')
    
    # Performance tracking
    processing_time = db.Column(db.Float)  # seconds
    error_message = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', back_populates='digest_records')
    
    def __repr__(self):
        return f'<DigestRecord {self.id} for user {self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'generated_at': self.generated_at.isoformat(),
            'email_count': self.email_count,
            'meeting_count': self.meeting_count,
            'data_source': self.data_source,
            'processing_time': self.processing_time,
            'success': self.error_message is None
        }


class MicrosoftToken(db.Model):
    """
    Model for storing Microsoft OAuth tokens securely
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        access_token: Encrypted access token
        refresh_token: Encrypted refresh token
        token_expires_at: Token expiration timestamp
        scope: OAuth scopes granted
        created_at: Token creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = 'microsoft_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Token data (should be encrypted in production)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    scope = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='microsoft_tokens')
    
    def __repr__(self):
        return f'<MicrosoftToken for user {self.user_id}>'
    
    @property
    def is_expired(self):
        """Check if token is expired"""
        if not self.token_expires_at:
            return True
        return datetime.utcnow() > self.token_expires_at
    
    def update_tokens(self, access_token, refresh_token=None, expires_at=None, scope=None):
        """
        Update token data
        
        Args:
            access_token (str): New access token
            refresh_token (str): New refresh token (optional)
            expires_at (datetime): Token expiration time
            scope (str): OAuth scopes
        """
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if expires_at:
            self.token_expires_at = expires_at
        if scope:
            self.scope = scope
        self.updated_at = datetime.utcnow()
        db.session.commit()


class UserSettings(db.Model):
    """
    Model for storing user-specific settings
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        settings_data: JSON blob of user settings
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    settings_data = db.Column(db.JSON, default=dict)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='settings')
    
    # Default settings
    DEFAULT_SETTINGS = {
        'digest_time': '09:00',
        'timezone': 'UTC',
        'privacy_mode': True,
        'working_hours_start': 9,
        'working_hours_end': 17,
        'use_test_data': False,
        'email_notifications': True,
        'digest_format': 'html'  # 'html' or 'text'
    }
    
    def __repr__(self):
        return f'<UserSettings for user {self.user_id}>'
    
    def get_setting(self, key, default=None):
        """
        Get a specific setting value
        
        Args:
            key (str): Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        settings = self.settings_data or {}
        return settings.get(key, self.DEFAULT_SETTINGS.get(key, default))
    
    def update_setting(self, key, value):
        """
        Update a specific setting
        
        Args:
            key (str): Setting key
            value: Setting value
        """
        if not self.settings_data:
            self.settings_data = {}
        self.settings_data[key] = value
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_settings(self, settings_dict):
        """
        Update multiple settings at once
        
        Args:
            settings_dict (dict): Dictionary of settings to update
        """
        if not self.settings_data:
            self.settings_data = {}
        self.settings_data.update(settings_dict)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Get all settings as dictionary"""
        base_settings = self.DEFAULT_SETTINGS.copy()
        if self.settings_data:
            base_settings.update(self.settings_data)
        return base_settings


class DailyUsage(db.Model):
    """
    Model for tracking daily digest usage per user
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        usage_date: Date of usage
        digest_count: Number of digests generated
        first_generation_at: First generation timestamp
        last_generation_at: Last generation timestamp
    """
    __tablename__ = 'daily_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    usage_date = db.Column(db.Date, nullable=False)
    digest_count = db.Column(db.Integer, default=0)
    first_generation_at = db.Column(db.DateTime)
    last_generation_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='daily_usage')
    
    # Unique constraint on user_id and usage_date
    __table_args__ = (
        db.UniqueConstraint('user_id', 'usage_date', name='_user_date_uc'),
    )
    
    def __repr__(self):
        return f'<DailyUsage {self.user_id} on {self.usage_date}>'
    
    def increment_usage(self):
        """Increment usage count and update timestamps"""
        self.digest_count += 1
        now = datetime.utcnow()
        if not self.first_generation_at:
            self.first_generation_at = now
        self.last_generation_at = now
        db.session.commit()
