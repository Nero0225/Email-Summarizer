"""
Services module

This module contains business logic services that handle
the core functionality of the Email Summarizer application.
"""

# Import services for easy access
from app.services.user_service import UserService
from app.services.digest_service import DigestService
from app.services.microsoft_service import MicrosoftService
from app.services.email_service import EmailService
from app.services.calendar_service import CalendarService
from app.services.privacy_service import PrivacyService

__all__ = [
    'UserService',
    'DigestService',
    'MicrosoftService',
    'EmailService',
    'CalendarService',
    'PrivacyService'
]
