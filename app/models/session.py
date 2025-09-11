"""
User Session Model

This module defines the UserSession model for tracking active user sessions.
"""
from datetime import datetime, timedelta
from app import db


class UserSession(db.Model):
    """
    Model for tracking active user sessions
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        session_id: Unique session identifier
        ip_address: User's IP address
        user_agent: User's browser/agent info
        login_at: Session start time
        last_activity: Last activity timestamp
        expires_at: Session expiration time
        is_active: Whether session is active
    """
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))  # Supports IPv6
    user_agent = db.Column(db.String(255))
    login_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='sessions')
    
    def __init__(self, user_id, session_id, ip_address=None, user_agent=None, duration_hours=24):
        """Initialize a new session"""
        self.user_id = user_id
        self.session_id = session_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.login_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        self.is_active = True
    
    def __repr__(self):
        return f'<UserSession {self.session_id} for user {self.user_id}>'
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    
    def deactivate(self):
        """Deactivate the session"""
        self.is_active = False
        db.session.commit()
    
    @property
    def is_expired(self):
        """Check if session has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def duration(self):
        """Get session duration"""
        end_time = self.last_activity if self.is_active else self.expires_at
        return end_time - self.login_at
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired sessions"""
        expired = cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired:
            db.session.delete(session)
        
        db.session.commit()
        return len(expired)
    
    @classmethod
    def get_active_sessions(cls):
        """Get all active, non-expired sessions"""
        return cls.query.filter(
            cls.is_active == True,
            cls.expires_at > datetime.utcnow()
        ).order_by(cls.last_activity.desc()).all()
    
    @classmethod
    def terminate_user_sessions(cls, user_id):
        """Terminate all sessions for a user"""
        sessions = cls.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        for session in sessions:
            session.deactivate()
        
        return len(sessions)
