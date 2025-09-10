"""
Email Summarizer Application Factory

This module contains the Flask application factory pattern implementation
for creating and configuring the email summarizer application.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from flask_cors import CORS
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
session = Session()
cors = CORS()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name='development'):
    """
    Application factory pattern for creating Flask app instances
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    session.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config.get('ALLOWED_ORIGINS', '*'),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configure login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.admin import admin_bp
    from app.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Configure logging
    if not app.debug and not app.testing:
        configure_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Register template filters and context processors
    register_template_utilities(app)
    
    return app


def configure_logging(app):
    """
    Configure application logging
    
    Args:
        app (Flask): Flask application instance
    """
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    file_handler = RotatingFileHandler(
        'logs/email_summarizer.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Email Summarizer startup')


def register_error_handlers(app):
    """
    Register error handlers for the application
    
    Args:
        app (Flask): Flask application instance
    """
    from app.utils.errors import handle_404, handle_500, handle_403, handle_api_error
    
    app.register_error_handler(404, handle_404)
    app.register_error_handler(403, handle_403)
    app.register_error_handler(500, handle_500)
    app.register_error_handler(Exception, handle_api_error)


def register_cli_commands(app):
    """
    Register CLI commands for the application
    
    Args:
        app (Flask): Flask application instance
    """
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database with tables and default data."""
        from app.models import User
        db.create_all()
        print('Initialized the database.')
        
        # Create default admin user if not exists
        from app.services.user_service import UserService
        user_service = UserService()
        
        if not user_service.get_user_by_username('admin'):
            admin_password = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin123')
            user_service.create_user(
                username='admin',
                full_name='System Administrator',
                email='admin@emailsummarizer.com',
                password=admin_password,
                is_admin=True,
                auto_approve=True
            )
            print(f'Default admin user created (password: {admin_password})')
    
    @app.cli.command('create-admin')
    def create_admin_command():
        """Create a new admin user."""
        import getpass
        from app.services.user_service import UserService
        
        username = input('Username: ')
        full_name = input('Full Name: ')
        email = input('Email: ')
        password = getpass.getpass('Password: ')
        
        user_service = UserService()
        try:
            user_service.create_user(
                username=username,
                full_name=full_name,
                email=email,
                password=password,
                is_admin=True,
                auto_approve=True
            )
            print(f'Admin user {username} created successfully.')
        except ValueError as e:
            print(f'Error: {str(e)}')


def register_template_utilities(app):
    """
    Register template filters and context processors
    
    Args:
        app (Flask): Flask application instance
    """
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%Y-%m-%d %H:%M'):
        """Format datetime for display"""
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.context_processor
    def inject_config():
        """Inject common variables into all templates"""
        return {
            'app_name': app.config.get('APP_NAME', 'Email Summarizer'),
            'app_version': app.config.get('APP_VERSION', '1.0.0')
        }


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from app.models import User
    return User.query.get(int(user_id))
