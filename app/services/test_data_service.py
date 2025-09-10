"""
Test Data Service

This module provides sample data for testing and demonstration purposes
when Microsoft 365 integration is not available or configured.
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple


class TestDataService:
    """Service class for generating test/sample data"""
    
    def __init__(self):
        # Sample email templates
        self.email_templates = [
            {
                'subject': 'Project Apollo Launch - Final Slides',
                'sender': {'name': 'Sarah Chen', 'email': 'sarah.chen@company.com'},
                'body': 'Hi team,\n\nI\'ve completed the final revisions to the Apollo launch presentation. Can you please review and approve the slides before tomorrow\'s client meeting? The deck is in the shared folder.\n\nKey changes:\n- Updated market analysis (slides 5-8)\n- New competitive landscape section\n- Revised financial projections\n\nPlease reply by EOD today with your approval or any final comments.\n\nThanks,\nSarah',
                'importance': 'high',
                'has_attachments': True,
                'thread_count': 12
            },
            {
                'subject': 'IT Security Reminder - Password Reset Required',
                'sender': {'name': 'IT Helpdesk', 'email': 'it-support@company.com'},
                'body': 'Dear User,\n\nYour corporate password will expire in 3 days. Please reset your password before Friday to avoid account lockout.\n\nTo reset your password:\n1. Visit the corporate portal\n2. Click "Change Password"\n3. Follow the security requirements\n\nIf you need assistance, please contact the IT helpdesk at ext. 2020.\n\nBest regards,\nIT Security Team',
                'importance': 'high',
                'has_attachments': False,
                'thread_count': 4
            },
            {
                'subject': 'Team Offsite - Catering Options',
                'sender': {'name': 'Tom Richardson', 'email': 'tom.richardson@company.com'},
                'body': 'Hey everyone,\n\nFor next week\'s team offsite, we need to finalize the catering. I\'ve received quotes from three vendors:\n\n1. Gourmet Express - $45/person (Italian)\n2. Fresh Bites - $38/person (Mixed menu)\n3. Green Garden - $35/person (Vegetarian options)\n\nCan you all please vote on your preference? We need to confirm by Wednesday.\n\nAlso, please let me know about any dietary restrictions.\n\nThanks!\nTom',
                'importance': 'normal',
                'has_attachments': True,
                'thread_count': 7
            },
            {
                'subject': 'Client Feedback - Proposal Draft',
                'sender': {'name': 'Emma Li', 'email': 'emma.li@clientcorp.com'},
                'body': 'Hi Team,\n\nI\'ve reviewed the latest proposal draft with our stakeholders. Overall, the direction looks good, but we have some specific feedback:\n\n1. Timeline needs adjustment - Q2 milestones seem aggressive\n2. Budget breakdown needs more detail on Phase 2\n3. Can we add more case studies from similar industries?\n\nPlease address these points and send us a revised version by end of week. We\'re planning to present this to the board next Tuesday.\n\nBest,\nEmma',
                'importance': 'high',
                'has_attachments': True,
                'thread_count': 5
            },
            {
                'subject': 'Q4 Marketing Newsletter - October Edition',
                'sender': {'name': 'Marketing Team', 'email': 'newsletter@company.com'},
                'body': 'October Newsletter\n\nIn this month\'s edition:\n- New product launch success\n- Employee spotlight: Jane Doe\n- Upcoming events and webinars\n- Industry news and trends\n\nRead the full newsletter on our intranet.\n\nTo unsubscribe from this newsletter, click here.',
                'importance': 'low',
                'has_attachments': False,
                'thread_count': 1
            },
            {
                'subject': 'Budget Review Meeting - Action Items',
                'sender': {'name': 'Michael Zhang', 'email': 'michael.zhang@company.com'},
                'body': 'Team,\n\nFollowing today\'s budget review, here are the action items:\n\n1. Sarah - Update Q4 projections by Wednesday\n2. Tom - Compile vendor cost analysis\n3. Emma - Review and approve marketing spend\n\nCan someone else handle the facilities budget review? I\'m swamped with the Apollo project.\n\nLet\'s reconvene Friday to finalize everything.\n\nMichael',
                'importance': 'normal',
                'has_attachments': False,
                'thread_count': 3
            },
            {
                'subject': 'Urgent: Server Maintenance Tonight',
                'sender': {'name': 'DevOps Team', 'email': 'devops@company.com'},
                'body': 'URGENT NOTICE\n\nWe will be performing critical server maintenance tonight from 10 PM to 2 AM EST.\n\nAffected services:\n- Email servers\n- File storage\n- Internal applications\n\nPlease save all work and log out before 9:45 PM. Services will be intermittently available during this window.\n\nWe apologize for the short notice. This maintenance is required to address critical security patches.\n\nDevOps Team',
                'importance': 'high',
                'has_attachments': False,
                'thread_count': 1
            },
            {
                'subject': 'New Hire Introduction - Welcome Jane Smith',
                'sender': {'name': 'HR Department', 'email': 'hr@company.com'},
                'body': 'Dear Team,\n\nWe\'re pleased to announce that Jane Smith will be joining our Product Development team as Senior Product Manager starting next Monday.\n\nJane brings 8 years of experience from TechCorp and will be leading our mobile initiatives. She\'ll be based in our SF office.\n\nPlease join us for a welcome lunch on Monday at 12:30 PM in the main conference room.\n\nBest regards,\nHR Team',
                'importance': 'normal',
                'has_attachments': False,
                'thread_count': 1
            },
            {
                'subject': 'Schedule Design Review for New Feature',
                'sender': {'name': 'Alex Johnson', 'email': 'alex.johnson@company.com'},
                'body': 'Hi,\n\nWe need to schedule a design review for the new dashboard feature. The mockups are ready and we\'d like to get feedback from all stakeholders.\n\nProposed times next week:\n- Tuesday 2-3 PM\n- Thursday 10-11 AM\n- Friday 3-4 PM\n\nPlease let me know your availability. We\'ll need about an hour to go through everything.\n\nThanks,\nAlex',
                'importance': 'normal',
                'has_attachments': True,
                'thread_count': 2
            },
            {
                'subject': 'FYI: Industry Report - Mobile Trends 2024',
                'sender': {'name': 'Research Team', 'email': 'research@company.com'},
                'body': 'Team,\n\nFor your information, we\'ve published our latest industry report on mobile trends for 2024. Key findings include:\n\n- 73% increase in mobile commerce\n- AI integration becoming standard\n- Privacy concerns driving new regulations\n\nThe full report is available on the shared drive. No action required, just keeping everyone informed.\n\nResearch Team',
                'importance': 'low',
                'has_attachments': True,
                'thread_count': 1
            }
        ]
        
        # Sample calendar events
        self.calendar_templates = [
            {
                'subject': 'Project Apollo Check-In',
                'organizer': 'Sarah Chen',
                'duration': 60,
                'location': 'Conference Room A',
                'agenda': 'Review launch preparations, finalize client presentation deck, align on messaging for tomorrow\'s meeting.',
                'attendees': 5
            },
            {
                'subject': 'Marketing Strategy Review',
                'organizer': 'David Kim',
                'duration': 90,
                'location': 'Zoom Meeting',
                'agenda': 'Q4 campaign planning, budget allocation, review performance metrics from Q3.',
                'attendees': 8
            },
            {
                'subject': 'Client Feedback Call (ACME Corp)',
                'organizer': 'Emma Li',
                'duration': 45,
                'location': 'Teams Meeting',
                'agenda': 'Walk through proposal feedback, discuss timeline adjustments, agree on next revision deadline.',
                'attendees': 4
            },
            {
                'subject': '1:1 with Manager',
                'organizer': 'Alex Johnson',
                'duration': 30,
                'location': 'Office 304',
                'agenda': 'Weekly update, discuss upcoming projects, address any blockers or concerns.',
                'attendees': 2
            },
            {
                'subject': 'All-Hands Meeting',
                'organizer': 'CEO',
                'duration': 60,
                'location': 'Main Auditorium + Zoom',
                'agenda': 'Company updates, Q3 results, Q4 priorities, employee recognition.',
                'attendees': 150
            },
            {
                'subject': 'Design Sprint Planning',
                'organizer': 'UX Team Lead',
                'duration': 120,
                'location': 'Design Studio',
                'agenda': 'Plan next week\'s design sprint, assign roles, review user research findings.',
                'attendees': 6
            }
        ]
    
    def get_sample_data(self, email_count: int = 15, meeting_count: int = 4) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get sample emails and calendar events
        
        Args:
            email_count: Number of emails to generate
            meeting_count: Number of meetings to generate
            
        Returns:
            Tuple of (emails, calendar_events)
        """
        emails = self._generate_emails(email_count)
        calendar_events = self._generate_calendar_events(meeting_count)
        
        return emails, calendar_events
    
    def _generate_emails(self, count: int) -> List[Dict[str, Any]]:
        """Generate sample emails"""
        emails = []
        now = datetime.utcnow()
        
        # Use templates and generate variations
        for i in range(count):
            template = self.email_templates[i % len(self.email_templates)]
            
            # Generate conversation ID (some emails share conversation)
            if template['thread_count'] > 1 and i > 0 and random.random() > 0.5:
                # Part of existing conversation
                conversation_id = emails[-1].get('conversationId')
            else:
                conversation_id = str(uuid.uuid4())
            
            # Calculate received time (spread over last 2 days)
            hours_ago = random.randint(0, 48)
            received_time = now - timedelta(hours=hours_ago, minutes=random.randint(0, 59))
            
            email = {
                'id': str(uuid.uuid4()),
                'conversationId': conversation_id,
                'subject': template['subject'],
                'bodyPreview': template['body'][:200] + '...' if len(template['body']) > 200 else template['body'],
                'body': {
                    'contentType': 'text',
                    'content': template['body']
                },
                'from': {
                    'emailAddress': {
                        'name': template['sender']['name'],
                        'address': template['sender']['email']
                    }
                },
                'receivedDateTime': received_time.isoformat() + 'Z',
                'importance': template['importance'],
                'hasAttachments': template['has_attachments'],
                'isRead': False
            }
            
            emails.append(email)
        
        return emails
    
    def _generate_calendar_events(self, count: int) -> List[Dict[str, Any]]:
        """Generate sample calendar events for today"""
        events = []
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Define possible meeting times
        time_slots = [
            (9, 0),   # 9:00 AM
            (10, 0),  # 10:00 AM
            (11, 30), # 11:30 AM
            (14, 0),  # 2:00 PM
            (15, 0),  # 3:00 PM
            (16, 0),  # 4:00 PM
        ]
        
        # Select random time slots
        selected_slots = random.sample(time_slots, min(count, len(time_slots)))
        
        for i, (hour, minute) in enumerate(selected_slots):
            template = self.calendar_templates[i % len(self.calendar_templates)]
            
            start_time = today.replace(hour=hour, minute=minute)
            end_time = start_time + timedelta(minutes=template['duration'])
            
            # Determine if online
            is_online = 'zoom' in template['location'].lower() or 'teams' in template['location'].lower()
            
            event = {
                'id': str(uuid.uuid4()),
                'subject': template['subject'],
                'start': {
                    'dateTime': start_time.isoformat() + 'Z',
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': end_time.isoformat() + 'Z',
                    'timeZone': 'UTC'
                },
                'location': {
                    'displayName': template['location']
                },
                'organizer': {
                    'emailAddress': {
                        'name': template['organizer'],
                        'address': f"{template['organizer'].lower().replace(' ', '.')}@company.com"
                    }
                },
                'attendees': [
                    {
                        'type': 'required',
                        'emailAddress': {
                            'name': f'Attendee {j}',
                            'address': f'attendee{j}@company.com'
                        }
                    } for j in range(template['attendees'])
                ],
                'body': {
                    'contentType': 'text',
                    'content': template['agenda']
                },
                'isOnlineMeeting': is_online,
                'showAs': 'busy',
                'importance': 'normal',
                'isAllDay': False,
                'isCancelled': False
            }
            
            events.append(event)
        
        # Sort by start time
        events.sort(key=lambda x: x['start']['dateTime'])
        
        return events
    
    def get_test_user_profile(self) -> Dict[str, Any]:
        """Get test user profile data"""
        return {
            'displayName': 'Test User',
            'mail': 'testuser@company.com',
            'userPrincipalName': 'testuser@company.com',
            'id': str(uuid.uuid4()),
            'jobTitle': 'Product Manager',
            'department': 'Product Development',
            'officeLocation': 'San Francisco'
        }
    
    def generate_digest_preview(self) -> Dict[str, Any]:
        """Generate a preview digest for demonstration"""
        emails, events = self.get_sample_data(20, 5)
        
        # Create mock processed data
        from app.services.email_service import EmailService
        from app.services.calendar_service import CalendarService
        from app.services.digest_generator import StructuredDigestGenerator
        
        email_service = EmailService()
        calendar_service = CalendarService()
        digest_generator = StructuredDigestGenerator()
        
        # Process emails
        conversations = {}
        for email in emails:
            conv_id = email['conversationId']
            if conv_id not in conversations:
                conversations[conv_id] = []
            conversations[conv_id].append(email)
        
        processed_emails = email_service.process_emails(emails)
        processed_calendar = calendar_service.process_events(events)
        
        # Generate digest
        digest = digest_generator.generate_digest(
            processed_emails,
            processed_calendar,
            "Test User"
        )
        
        return digest
