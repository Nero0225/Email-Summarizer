"""
Digest Service

This module handles digest generation including email and calendar
processing, 4D classification, and structured digest creation.
"""
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple, List
from flask import current_app
from app import db
from app.models import User, DigestRecord, DailyUsage, MicrosoftToken
from app.services.microsoft_service import MicrosoftService
from app.services.email_service import EmailService
from app.services.calendar_service import CalendarService
from app.services.privacy_service import PrivacyService
from app.services.digest_generator import StructuredDigestGenerator


class DigestService:
    """Service class for digest generation operations"""
    
    def __init__(self):
        self.microsoft_service = MicrosoftService()
        self.email_service = EmailService()
        self.calendar_service = CalendarService()
        self.privacy_service = PrivacyService()
        self.digest_generator = StructuredDigestGenerator()
    
    def generate_digest_for_user(self, user_id: int, **options) -> Dict[str, Any]:
        """
        Generate daily digest for a specific user
        
        Args:
            user_id: User ID
            **options: Additional options (force_refresh, include_raw_data)
            
        Returns:
            Dictionary with generation result
        """
        start_time = time.time()
        
        try:
            # Get user and validate
            user = User.query.get(user_id)
            if not user:
                return {
                    'status': 'error',
                    'error_type': 'user_not_found',
                    'message': 'User not found'
                }
            
            # Check daily limit
            if not self._can_generate_today(user_id):
                return {
                    'status': 'error',
                    'error_type': 'daily_limit',
                    'message': "You've already generated today's digest. Please try again tomorrow."
                }
            
            # Get user settings
            settings = user.settings.to_dict() if user.settings else {}
            
            # Get email and calendar data
            emails_data, calendar_data, data_source = self._fetch_user_data(user, settings)
            
            if emails_data is None:
                return {
                    'status': 'error',
                    'error_type': 'data_fetch_failed',
                    'message': 'Failed to fetch email and calendar data'
                }
            
            # Apply privacy redaction if enabled
            if settings.get('privacy_mode', True):
                emails_data = self._apply_privacy_redaction(emails_data)
            
            # Process emails and calendar
            processed_emails = self.email_service.process_emails(emails_data)
            processed_calendar = self.calendar_service.process_events(
                calendar_data,
                working_hours=(
                    settings.get('working_hours_start', 9),
                    settings.get('working_hours_end', 17)
                )
            )
            
            # Generate structured digest
            digest_data = self.digest_generator.generate_digest(
                processed_emails,
                processed_calendar,
                user.full_name
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save digest record
            digest_record = DigestRecord(
                user_id=user_id,
                email_count=digest_data['metadata']['total_emails'],
                meeting_count=digest_data['metadata']['total_meetings'],
                digest_data=digest_data,
                data_source=data_source,
                processing_time=processing_time
            )
            db.session.add(digest_record)
            
            # Update daily usage
            self._update_daily_usage(user_id)
            
            # Commit all changes
            db.session.commit()
            
            current_app.logger.info(
                f'Digest generated for user {user_id} in {processing_time:.2f}s'
            )
            
            result = {
                'status': 'success',
                'digest_id': digest_record.id,
                'generated_at': digest_record.generated_at.isoformat(),
                'processing_time': processing_time,
                'email_count': digest_record.email_count,
                'meeting_count': digest_record.meeting_count,
                'data_source': data_source
            }
            
            if options.get('include_raw_data'):
                result['digest_data'] = digest_data
            
            return result
            
        except Exception as e:
            # Log error
            current_app.logger.error(f'Digest generation error for user {user_id}: {str(e)}')
            
            # Save failed digest record
            try:
                digest_record = DigestRecord(
                    user_id=user_id,
                    error_message=str(e),
                    processing_time=time.time() - start_time
                )
                db.session.add(digest_record)
                db.session.commit()
            except:
                pass
            
            return {
                'status': 'error',
                'error_type': 'generation_failed',
                'message': f'Failed to generate digest: {str(e)}'
            }
    
    def _can_generate_today(self, user_id: int) -> bool:
        """Check if user can generate digest today"""
        today = date.today()
        daily_usage = DailyUsage.query.filter_by(
            user_id=user_id,
            usage_date=today
        ).first()
        
        daily_limit = current_app.config.get('DAILY_DIGEST_LIMIT', 1)
        return not daily_usage or daily_usage.digest_count < daily_limit
    
    def _update_daily_usage(self, user_id: int):
        """Update daily usage tracking"""
        today = date.today()
        daily_usage = DailyUsage.query.filter_by(
            user_id=user_id,
            usage_date=today
        ).first()
        
        if daily_usage:
            daily_usage.increment_usage()
        else:
            daily_usage = DailyUsage(
                user_id=user_id,
                usage_date=today,
                digest_count=1,
                first_generation_at=datetime.utcnow(),
                last_generation_at=datetime.utcnow()
            )
            db.session.add(daily_usage)
    
    def _fetch_user_data(self, user: User, settings: Dict[str, Any]) -> Tuple[List, List, str]:
        """
        Fetch email and calendar data for user
        
        Returns:
            Tuple of (emails, calendar_events, data_source)
        """
        # Check if using test data
        if settings.get('use_test_data', False) or not user.has_microsoft_linked:
            return self._get_test_data(settings)
        
        # Fetch from Microsoft 365
        try:
            # Get valid access token
            access_token = self._ensure_valid_token(user)
            if not access_token:
                raise Exception('Failed to obtain valid access token')
            
            # Fetch emails
            emails = self.microsoft_service.get_user_emails(
                access_token,
                days_back=2  # Per PRD: today + yesterday (+ weekend if Monday)
            )
            
            # Fetch calendar events
            calendar_events = self.microsoft_service.get_user_calendar_events(
                access_token
            )
            
            return emails, calendar_events, 'office365'
            
        except Exception as e:
            current_app.logger.error(f'Failed to fetch Office 365 data: {str(e)}')
            # Fall back to test data
            return self._get_test_data(settings)
    
    def _ensure_valid_token(self, user: User) -> Optional[str]:
        """Ensure user has valid access token"""
        if not user.microsoft_tokens:
            return None
        
        tokens = user.microsoft_tokens
        
        # Check if token is expired
        if tokens.is_expired:
            # Try to refresh
            if tokens.refresh_token:
                try:
                    result = self.microsoft_service.refresh_token(tokens.refresh_token)
                    if result and 'access_token' in result:
                        # Update tokens
                        expires_at = datetime.utcnow() + timedelta(
                            seconds=result.get('expires_in', 3600)
                        )
                        tokens.update_tokens(
                            access_token=result['access_token'],
                            refresh_token=result.get('refresh_token', tokens.refresh_token),
                            expires_at=expires_at
                        )
                        return result['access_token']
                except Exception as e:
                    current_app.logger.error(f'Token refresh failed: {str(e)}')
                    return None
            return None
        
        return tokens.access_token
    
    def _get_test_data(self, settings: Dict[str, Any]) -> Tuple[List, List, str]:
        """Get test data for demonstration"""
        from app.services.test_data_service import TestDataService
        
        test_service = TestDataService()
        emails, calendar_events = test_service.get_sample_data()
        return emails, calendar_events, 'test_data'
    
    def _apply_privacy_redaction(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply privacy redaction to emails"""
        redacted_emails = []
        
        for email in emails:
            redacted_email, redaction_map = self.privacy_service.redact_email(email)
            # Store redaction map for potential reconstruction
            redacted_email['_redaction_map'] = redaction_map
            redacted_emails.append(redacted_email)
        
        return redacted_emails
    
    def get_digest_by_id(self, digest_id: int, user_id: int) -> Optional[DigestRecord]:
        """
        Get digest by ID with user validation
        
        Args:
            digest_id: Digest ID
            user_id: User ID for validation
            
        Returns:
            DigestRecord if found and belongs to user, None otherwise
        """
        digest = DigestRecord.query.filter_by(
            id=digest_id,
            user_id=user_id
        ).first()
        
        return digest
    
    def get_user_digest_history(self, user_id: int, limit: int = 10) -> List[DigestRecord]:
        """
        Get user's digest history
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of DigestRecord objects
        """
        return DigestRecord.query.filter_by(
            user_id=user_id
        ).order_by(
            DigestRecord.generated_at.desc()
        ).limit(limit).all()
    
    def get_digest_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get digest statistics for user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of statistics
        """
        from sqlalchemy import func
        
        stats = db.session.query(
            func.count(DigestRecord.id).label('total_digests'),
            func.count(func.nullif(DigestRecord.error_message, None)).label('failed_digests'),
            func.avg(DigestRecord.processing_time).label('avg_processing_time'),
            func.sum(DigestRecord.email_count).label('total_emails_processed'),
            func.sum(DigestRecord.meeting_count).label('total_meetings_processed')
        ).filter_by(user_id=user_id).first()
        
        return {
            'total_digests': stats.total_digests or 0,
            'successful_digests': (stats.total_digests or 0) - (stats.failed_digests or 0),
            'failed_digests': stats.failed_digests or 0,
            'avg_processing_time': round(stats.avg_processing_time or 0, 2),
            'total_emails_processed': stats.total_emails_processed or 0,
            'total_meetings_processed': stats.total_meetings_processed or 0,
            'success_rate': round(
                ((stats.total_digests or 0) - (stats.failed_digests or 0)) / 
                max(stats.total_digests or 1, 1) * 100, 
                1
            )
        }
