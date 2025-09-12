"""
Flask Session Storage Model

This module provides database-based session storage for Flask-Session
to replace filesystem-based storage and prevent disk space issues.
"""
from datetime import datetime
from app import db


class FlaskSession(db.Model):
    """Model for storing Flask session data in the database"""
    __tablename__ = 'flask_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    data = db.Column(db.LargeBinary)  # Stores pickled session data
    expiry = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<FlaskSession {self.session_id}>'
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired sessions from the database"""
        expired_count = cls.query.filter(
            cls.expiry < datetime.utcnow()
        ).delete()
        db.session.commit()
        return expired_count
