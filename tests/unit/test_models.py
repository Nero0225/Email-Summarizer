"""
Unit tests for database models
"""
import pytest
from datetime import datetime
from app import db
from app.models import User, UserStatus, UserRole, UserSettings, DigestRecord


class TestUserModel:
    """Test User model functionality"""
    
    def test_create_user(self, app):
        """Test user creation"""
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            role=UserRole.USER,
            status=UserStatus.PENDING
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        # Verify user was created
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('password123')
        assert not user.check_password('wrongpass')
    
    def test_user_roles(self, app):
        """Test user role functionality"""
        # Regular user
        user = User(
            username='user',
            email='user@example.com',
            full_name='Regular User',
            role=UserRole.USER
        )
        assert not user.is_admin
        
        # Admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Admin User',
            role=UserRole.ADMIN
        )
        assert admin.is_admin
    
    def test_user_status(self, app):
        """Test user status functionality"""
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            status=UserStatus.PENDING
        )
        
        # Pending user is not active
        assert not user.is_active
        
        # Approve user
        admin = User(username='admin', email='admin@example.com', full_name='Admin')
        user.approve(admin)
        
        assert user.status == UserStatus.APPROVED
        assert user.is_active
        assert user.approved_at is not None
        assert user.approved_by == admin
    
    def test_microsoft_account_linking(self, app):
        """Test Microsoft account linking"""
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User'
        )
        
        # Initially no Microsoft account
        assert not user.has_microsoft_linked
        assert user.microsoft_account_email is None
        
        # Link account
        user.link_microsoft_account('test@microsoft.com')
        
        assert user.has_microsoft_linked
        assert user.microsoft_account_email == 'test@microsoft.com'
        assert user.microsoft_account_linked_at is not None
        
        # Unlink account
        user.unlink_microsoft_account()
        
        assert not user.has_microsoft_linked
        assert user.microsoft_account_email is None


class TestUserSettings:
    """Test UserSettings model functionality"""
    
    def test_default_settings(self, app):
        """Test default settings creation"""
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User'
        )
        settings = UserSettings(user=user)
        
        db.session.add(user)
        db.session.add(settings)
        db.session.commit()
        
        # Check defaults
        assert settings.get_setting('digest_time') == '09:00'
        assert settings.get_setting('timezone') == 'UTC'
        assert settings.get_setting('privacy_mode') is True
        assert settings.get_setting('working_hours_start') == 9
        assert settings.get_setting('working_hours_end') == 17
    
    def test_update_settings(self, app):
        """Test updating settings"""
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User'
        )
        settings = UserSettings(user=user)
        
        db.session.add(user)
        db.session.add(settings)
        db.session.commit()
        
        # Update single setting
        settings.update_setting('digest_time', '08:30')
        assert settings.get_setting('digest_time') == '08:30'
        
        # Update multiple settings
        settings.update_settings({
            'timezone': 'US/Eastern',
            'privacy_mode': False,
            'working_hours_start': 8
        })
        
        assert settings.get_setting('timezone') == 'US/Eastern'
        assert settings.get_setting('privacy_mode') is False
        assert settings.get_setting('working_hours_start') == 8


class TestDigestRecord:
    """Test DigestRecord model functionality"""
    
    def test_create_digest_record(self, app):
        """Test digest record creation"""
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User'
        )
        db.session.add(user)
        db.session.commit()
        
        digest = DigestRecord(
            user_id=user.id,
            email_count=25,
            meeting_count=3,
            digest_data={'test': 'data'},
            data_source='office365',
            processing_time=2.5
        )
        
        db.session.add(digest)
        db.session.commit()
        
        assert digest.id is not None
        assert digest.user_id == user.id
        assert digest.email_count == 25
        assert digest.meeting_count == 3
        assert digest.processing_time == 2.5
        assert digest.error_message is None
    
    def test_failed_digest_record(self, app):
        """Test failed digest record"""
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User'
        )
        db.session.add(user)
        db.session.commit()
        
        digest = DigestRecord(
            user_id=user.id,
            error_message='API connection failed',
            processing_time=0.5
        )
        
        db.session.add(digest)
        db.session.commit()
        
        assert digest.error_message == 'API connection failed'
        assert digest.email_count == 0
        assert digest.meeting_count == 0
