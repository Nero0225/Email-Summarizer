"""
Database Session Interface for Flask

This module provides a custom session interface that stores session data
in the database instead of the filesystem.
"""
import pickle
from datetime import datetime, timedelta
from uuid import uuid4
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
from flask import Flask


class SqlAlchemySession(CallbackDict, SessionMixin):
    """Session object that tracks modifications"""
    
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update=on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class SqlAlchemySessionInterface(SessionInterface):
    """Session interface that uses SQLAlchemy for storage"""
    
    serializer = pickle
    session_class = SqlAlchemySession
    
    def __init__(self, app: Flask = None, db_session=None, table_name='flask_sessions', 
                 key_prefix='session:', use_signer=False, permanent=True):
        self.db_session = db_session
        self.key_prefix = key_prefix
        self.use_signer = use_signer
        self.permanent = permanent
        self.has_same_site_capability = hasattr(self, "get_cookie_samesite")
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the session interface with the Flask app"""
        app.session_interface = self
    
    def generate_sid(self):
        """Generate a new session ID"""
        return str(uuid4())
    
    def get_redis_expiration_time(self, app, session):
        """Get expiration time for the session"""
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)
    
    def open_session(self, app, request):
        """Open a session - load from database or create new"""
        from app import db
        from app.models import FlaskSession
        
        sid = request.cookies.get(app.config.get('SESSION_COOKIE_NAME'))
        
        if not sid:
            # Create new session
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)
        
        # Try to load session from database
        stored_session = FlaskSession.query.filter_by(session_id=sid).first()
        
        if stored_session:
            # Check if expired
            if stored_session.expiry > datetime.utcnow():
                try:
                    data = self.serializer.loads(stored_session.data)
                    return self.session_class(data, sid=sid)
                except:
                    # Corrupted session data, create new
                    return self.session_class(sid=sid, new=True)
            else:
                # Expired session, delete it
                db.session.delete(stored_session)
                db.session.commit()
        
        # No valid session found, create new with same ID to maintain cookie
        return self.session_class(sid=sid, new=True)
    
    def save_session(self, app, session, response):
        """Save the session to database"""
        from app import db
        from app.models import FlaskSession
        
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        
        # If session is empty and was new, don't save
        if not session and session.new:
            return
        
        # Get cookie settings
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        samesite = None
        if self.has_same_site_capability:
            samesite = self.get_cookie_samesite(app)
        
        # Calculate expiry
        if session.permanent:
            expiry_time = datetime.utcnow() + app.permanent_session_lifetime
        else:
            expiry_time = datetime.utcnow() + timedelta(days=1)
        
        # Save or update session in database
        if session.modified or session.new:
            # Serialize session data
            val = self.serializer.dumps(dict(session))
            
            # Check if session exists
            stored_session = FlaskSession.query.filter_by(session_id=session.sid).first()
            
            if stored_session:
                # Update existing session
                stored_session.data = val
                stored_session.expiry = expiry_time
            else:
                # Create new session record
                stored_session = FlaskSession(
                    session_id=session.sid,
                    data=val,
                    expiry=expiry_time
                )
                db.session.add(stored_session)
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Failed to save session: {e}")
                return
        
        # Set cookie
        if session:
            response.set_cookie(
                app.config.get('SESSION_COOKIE_NAME'),
                session.sid,
                expires=expiry_time,
                httponly=httponly,
                domain=domain,
                path=path,
                secure=secure,
                samesite=samesite
            )
        else:
            # Delete cookie if session is empty
            response.delete_cookie(
                app.config.get('SESSION_COOKIE_NAME'),
                domain=domain,
                path=path
            )
