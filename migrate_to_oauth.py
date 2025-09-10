#!/usr/bin/env python
"""
Migration script to support OAuth authentication flow

This script helps migrate existing databases to support the new OAuth authentication flow.
It does NOT modify existing user accounts but prepares the system for OAuth users.
"""
import os
import sys
from app import create_app, db
from app.models import User, UserRole

def migrate_to_oauth():
    """Perform migration steps for OAuth support"""
    print("Starting OAuth migration...")
    
    # Create application context
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Get admin email domains from config
        admin_domains = app.config.get('ADMIN_EMAIL_DOMAINS', [])
        
        if admin_domains:
            print(f"\nConfigured admin email domains: {', '.join(admin_domains)}")
        else:
            print("\n⚠️  Warning: No admin email domains configured in ADMIN_EMAIL_DOMAINS")
            print("   Users from these domains will automatically get admin privileges during OAuth registration.")
        
        # Check for existing OAuth users
        oauth_users = User.query.filter(
            User.password_hash == None,
            User.microsoft_account_email != None
        ).all()
        
        print(f"\nExisting OAuth users: {len(oauth_users)}")
        
        # Check for users that could be admins based on email domain
        potential_admins = []
        regular_users = User.query.filter(User.role == UserRole.USER).all()
        
        for user in regular_users:
            for domain in admin_domains:
                if user.email.endswith(f'@{domain}'):
                    potential_admins.append(user)
                    break
        
        if potential_admins:
            print(f"\nFound {len(potential_admins)} users who could be admins based on email domain:")
            for user in potential_admins:
                print(f"  - {user.username} ({user.email})")
            
            upgrade = input("\nWould you like to upgrade these users to admin? (y/N): ")
            if upgrade.lower() == 'y':
                for user in potential_admins:
                    user.role = UserRole.ADMIN
                    print(f"  ✓ Upgraded {user.username} to admin")
                db.session.commit()
                print("\nAdmin upgrades completed.")
        
        print("\n✅ OAuth migration completed successfully!")
        print("\nNext steps:")
        print("1. Ensure ADMIN_EMAIL_DOMAINS is configured in your .env file")
        print("2. Configure Microsoft Azure App for OAuth (see AZURE_SETUP.md)")
        print("3. New users can now register using 'Sign in with Microsoft'")
        print("4. Existing users can link their Microsoft accounts in Settings")

if __name__ == '__main__':
    try:
        migrate_to_oauth()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)
