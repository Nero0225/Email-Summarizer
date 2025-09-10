"""
Test suite for Email Summarizer application

This module initializes the test configuration and provides
common fixtures and utilities for testing.
"""
import os
import tempfile
import pytest
from app import create_app, db
from app.models import User, UserRole, UserStatus


@pytest.fixture
def app():
    """Create application for testing"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure test app
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    # Create application context
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(client):
    """Create authenticated headers for API testing"""
    # Create test user
    user = User(
        username='testuser',
        email='test@example.com',
        full_name='Test User',
        role=UserRole.USER,
        status=UserStatus.APPROVED
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    # Login
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    # Return headers with session cookie
    return {'Cookie': response.headers.get('Set-Cookie')}


@pytest.fixture
def admin_user():
    """Create admin user for testing"""
    admin = User(
        username='admin',
        email='admin@example.com',
        full_name='Admin User',
        role=UserRole.ADMIN,
        status=UserStatus.APPROVED
    )
    admin.set_password('adminpass123')
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def sample_emails():
    """Provide sample email data for testing"""
    return [
        {
            'id': 'email1',
            'conversationId': 'conv1',
            'subject': 'Test Email 1',
            'bodyPreview': 'This is a test email',
            'from': {
                'emailAddress': {
                    'name': 'Sender 1',
                    'address': 'sender1@example.com'
                }
            },
            'receivedDateTime': '2024-01-01T10:00:00Z',
            'importance': 'normal',
            'hasAttachments': False
        },
        {
            'id': 'email2',
            'conversationId': 'conv1',
            'subject': 'Re: Test Email 1',
            'bodyPreview': 'Reply to test email',
            'from': {
                'emailAddress': {
                    'name': 'Sender 2',
                    'address': 'sender2@example.com'
                }
            },
            'receivedDateTime': '2024-01-01T11:00:00Z',
            'importance': 'high',
            'hasAttachments': True
        }
    ]


@pytest.fixture
def sample_events():
    """Provide sample calendar event data for testing"""
    return [
        {
            'id': 'event1',
            'subject': 'Team Meeting',
            'start': {
                'dateTime': '2024-01-01T09:00:00Z',
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': '2024-01-01T10:00:00Z',
                'timeZone': 'UTC'
            },
            'organizer': {
                'emailAddress': {
                    'name': 'Manager',
                    'address': 'manager@example.com'
                }
            },
            'location': {
                'displayName': 'Conference Room A'
            },
            'attendees': [],
            'body': {
                'contentType': 'text',
                'content': 'Weekly team sync'
            }
        }
    ]
