"""
Configuration module for Email Summarizer application

This module contains configuration classes for different environments
(development, testing, production) and handles environment variables.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'))


class Config:
    """Base configuration class with common settings"""
    
    # Application settings
    APP_NAME = os.getenv('APP_NAME', 'Email Summarizer')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    DATABASE_QUERY_TIMEOUT = 0.5  # Log slow queries (500ms)
    
    # Session configuration
    SESSION_TYPE = 'sqlalchemy'  # Changed from filesystem to sqlalchemy
    SESSION_SQLALCHEMY_TABLE = 'flask_sessions'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_NAME = 'email_summarizer_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Optional: Add session cleanup settings
    SESSION_CLEANUP_ENABLED = True
    SESSION_CLEANUP_INTERVAL = timedelta(hours=1)
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Microsoft Azure/Graph API settings
    AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
    AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID', 'common')
    REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/auth/callback')
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Email summarization settings
    MAX_EMAILS_PER_DIGEST = int(os.getenv('MAX_EMAILS_PER_DIGEST', 200))
    DIGEST_GENERATION_TIMEOUT = int(os.getenv('DIGEST_GENERATION_TIMEOUT', 300))  # 5 minutes
    # DAILY_DIGEST_LIMIT = int(os.getenv('DAILY_DIGEST_LIMIT', 1))  # Deprecated - no limit enforced
    
    # Working hours defaults
    DEFAULT_WORK_START_HOUR = int(os.getenv('DEFAULT_WORK_START_HOUR', 9))
    DEFAULT_WORK_END_HOUR = int(os.getenv('DEFAULT_WORK_END_HOUR', 17))
    DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'UTC')
    
    # Pagination
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))
    
    # CORS settings
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    
    # Rate limiting
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    # Admin settings
    ADMIN_EMAIL_DOMAINS = os.getenv('ADMIN_EMAIL_DOMAINS', 'admin.com,administrator.com').split(',')
    ADMIN_DEFAULT_PASSWORD = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin123')
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        pass


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'dev.db')
    )
    
    # Session cookies
    SESSION_COOKIE_SECURE = False
    
    # Development-specific settings
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    TEMPLATES_AUTO_RELOAD = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to console in development
        import logging
        from logging import StreamHandler
        stream_handler = StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(stream_handler)


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    DEBUG = True
    
    # Database - use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Session configuration for testing
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'flask_sessions'
    
    # Security
    SESSION_COOKIE_SECURE = False
    
    # Testing-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'prod.db')
    )
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production-specific settings
    PREFERRED_URL_SCHEME = 'https'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Email errors to admins
        import logging
        from logging.handlers import SMTPHandler
        
        credentials = None
        secure = None
        
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
                
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=[cls.MAIL_ADMIN],
            subject=f'{cls.APP_NAME} Application Error',
            credentials=credentials,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
