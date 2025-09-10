#!/usr/bin/env python3
"""
Database initialization script

This script initializes the database, creates tables, and adds default data.
Run this script after setting up your environment variables.
"""
import os
import sys
from app import create_app, db
from app.models import User, UserRole, UserStatus, UserSettings


def init_database():
    """Initialize the database with tables and default data"""
    # Create application context
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("\nCreating default admin user...")
            
            # Get admin password from environment or use default
            admin_password = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin123')
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@emailsummarizer.com',
                full_name='System Administrator',
                role=UserRole.ADMIN,
                status=UserStatus.APPROVED
            )
            admin.set_password(admin_password)
            
            # Create admin settings
            admin_settings = UserSettings(user=admin)
            
            # Save to database
            db.session.add(admin)
            db.session.add(admin_settings)
            db.session.commit()
            
            print(f"""
✅ Database initialized successfully!

Admin account created:
- Username: admin
- Password: {admin_password}

⚠️  IMPORTANT: 
1. This admin account uses traditional login. For production, use Microsoft OAuth.
2. Configure ADMIN_EMAIL_DOMAINS in .env to auto-assign admin privileges to specific email domains.
3. Users should register using Microsoft OAuth for secure authentication.

To start the application, run:
    python run.py
""")
        else:
            print("\n✅ Database already initialized. Admin user exists.")
            print("\nTo start the application, run:")
            print("    python run.py")


if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with your configuration")
        print("2. Set up a virtual environment and installed requirements")
        print("3. Configured your database connection string")
        sys.exit(1)
