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
            
            # Enrich digest data for the new template
            enriched_digest_data = self._enrich_digest_data(
                digest_data, 
                processed_emails, 
                processed_calendar
            )
            
            # Save digest record
            digest_record = DigestRecord(
                user_id=user_id,
                email_count=digest_data['metadata']['total_emails'],
                meeting_count=digest_data['metadata']['total_meetings'],
                digest_data=enriched_digest_data,
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
    
    def _enrich_digest_data(self, digest_data: Dict[str, Any], 
                          conversations: Dict[str, Any], 
                          calendar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich digest data with additional fields for the new template
        
        Args:
            digest_data: Base digest data from generator
            conversations: Processed email conversations
            calendar_data: Processed calendar data
            
        Returns:
            Enriched digest data
        """
        # Extract actions by type
        action_by_type = digest_data.get('sections', {}).get('actions', {}).get('by_category', {})
        
        # Calculate focus time blocks
        focus_blocks = self._calculate_focus_blocks(calendar_data)
        
        # Extract top senders and topics
        top_senders = self._extract_top_senders(conversations)
        key_topics = self._extract_key_topics(conversations)
        
        # Add enriched data
        enriched_data = {
            **digest_data,
            'focus_time_hours': calendar_data.get('focus_time_hours', 0),
            'focus_blocks': len(focus_blocks),
            'longest_block': max([block['hours'] for block in focus_blocks], default=0),
            'focus_blocks_data': focus_blocks[:3],  # Top 3 blocks
            'do_tasks': self._format_tasks(action_by_type.get('Do', [])),
            'delegate_tasks': self._format_tasks(action_by_type.get('Delegate', [])),
            'defer_tasks': self._format_tasks(action_by_type.get('Defer', [])),
            'delete_tasks': self._format_tasks(action_by_type.get('Delete', [])),
            'meetings': self._format_meetings(calendar_data.get('meetings', [])),
            'top_senders': top_senders[:5],
            'key_topics': key_topics[:10],
            'action_items': len(action_by_type.get('Do', [])) + len(action_by_type.get('Delegate', [])),
            'replies_needed': sum(1 for conv in conversations.values() if self._needs_reply(conv)),
            'high_priority': sum(1 for conv in conversations.values() if conv.get('importance') == 'high'),
            'attachments': sum(1 for conv in conversations.values() if conv.get('has_attachments', False))
        }
        
        return enriched_data
    
    def _calculate_focus_blocks(self, calendar_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate focus time blocks from calendar data"""
        meetings = calendar_data.get('meetings', [])
        if not meetings:
            # Full day available
            return [{
                'start': '9:00 AM',
                'end': '5:00 PM',
                'hours': 8,
                'type': 'full_day'
            }]
        
        focus_blocks = []
        work_start = 9  # 9 AM
        work_end = 17   # 5 PM
        
        # Sort meetings by start time
        sorted_meetings = sorted(meetings, key=lambda m: m.get('start_hour', 0))
        
        # Find gaps between meetings
        last_end = work_start
        for meeting in sorted_meetings:
            start_hour = meeting.get('start_hour', 0)
            if start_hour > last_end:
                gap_hours = start_hour - last_end
                if gap_hours >= 1:  # At least 1 hour
                    focus_blocks.append({
                        'start': f"{last_end}:00",
                        'end': f"{start_hour}:00",
                        'hours': gap_hours,
                        'type': 'between_meetings'
                    })
            last_end = meeting.get('end_hour', start_hour + 1)
        
        # Check for time after last meeting
        if last_end < work_end:
            focus_blocks.append({
                'start': f"{last_end}:00",
                'end': f"{work_end}:00",
                'hours': work_end - last_end,
                'type': 'end_of_day'
            })
        
        # Sort by duration
        focus_blocks.sort(key=lambda b: b['hours'], reverse=True)
        
        return focus_blocks
    
    def _extract_top_senders(self, conversations: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract top email senders"""
        sender_counts = {}
        
        for conv in conversations.values():
            sender = conv.get('latest_sender', {})
            if isinstance(sender, dict):
                sender_name = sender.get('name', 'Unknown')
                sender_email = sender.get('address', '')
            else:
                sender_name = str(sender)
                sender_email = ''
            
            key = f"{sender_name}|{sender_email}"
            sender_counts[key] = sender_counts.get(key, 0) + conv.get('email_count', 1)
        
        # Sort by count and format
        top_senders = []
        for sender_key, count in sorted(sender_counts.items(), key=lambda x: x[1], reverse=True):
            name, email = sender_key.split('|')
            top_senders.append({
                'name': name,
                'email': email,
                'count': count
            })
        
        return top_senders
    
    def _extract_key_topics(self, conversations: Dict[str, Any]) -> List[str]:
        """Extract key topics from email subjects and content"""
        topics = []
        topic_words = {}
        
        # Common words to exclude
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'about', 're:', 'fw:', 'fwd:', 'subject:'}
        
        for conv in conversations.values():
            subject = conv.get('subject', '').lower()
            # Extract meaningful words
            words = [w for w in subject.split() if len(w) > 3 and w not in stop_words]
            
            for word in words:
                topic_words[word] = topic_words.get(word, 0) + 1
        
        # Get most common topics
        sorted_topics = sorted(topic_words.items(), key=lambda x: x[1], reverse=True)
        
        # Format as title case
        for topic, count in sorted_topics[:20]:
            if count > 1:  # Only include topics that appear more than once
                topics.append(topic.title())
        
        return topics
    
    def _needs_reply(self, conversation: Dict[str, Any]) -> bool:
        """Check if conversation needs a reply"""
        # Check if it's classified as "Do" with high confidence
        classification = conversation.get('classification', {})
        if classification.get('action') == 'Do' and classification.get('confidence', 0) > 0.6:
            return True
        
        # Check for question marks in subject
        if '?' in conversation.get('subject', ''):
            return True
        
        # Check if latest email is from someone else (not the user)
        # This would require knowing the user's email, which we don't have here
        # So we'll use a simple heuristic
        return conversation.get('email_count', 0) % 2 == 1  # Odd number suggests awaiting reply
    
    def _format_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tasks for the template"""
        formatted_tasks = []
        for task in tasks[:10]:  # Limit to 10
            formatted_tasks.append({
                'subject': task.get('subject', 'No Subject'),
                'sender': task.get('sender', 'Unknown'),
                'confidence': task.get('confidence', 0),
                'reason': task.get('reason', '')
            })
        return formatted_tasks
    
    def _format_meetings(self, meetings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format meetings for the template"""
        formatted_meetings = []
        for meeting in meetings:
            formatted_meetings.append({
                'subject': meeting.get('subject', 'No Subject'),
                'start_time': meeting.get('time', '').split(' - ')[0] if ' - ' in meeting.get('time', '') else meeting.get('time', ''),
                'end_time': meeting.get('time', '').split(' - ')[1] if ' - ' in meeting.get('time', '') else '',
                'duration': meeting.get('duration_hours', 0),
                'location': meeting.get('location', ''),
                'organizer': meeting.get('organizer', 'Unknown'),
                'attendees': meeting.get('attendees', []),
                'attendee_count': meeting.get('attendee_count', 0),
                'is_online': meeting.get('is_online', False),
                'agenda': meeting.get('agenda', '')
            })
        return formatted_meetings
