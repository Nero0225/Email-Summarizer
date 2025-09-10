"""
Calendar Service

This module handles calendar event processing and analysis.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pytz


class CalendarService:
    """Service class for calendar processing operations"""
    
    def __init__(self):
        self.default_work_start = 9  # 9 AM
        self.default_work_end = 17   # 5 PM
    
    def process_events(self, events: List[Dict[str, Any]], 
                      working_hours: Tuple[int, int] = None) -> Dict[str, Any]:
        """
        Process calendar events according to PRD requirements
        
        Args:
            events: List of calendar events from Graph API
            working_hours: Tuple of (start_hour, end_hour)
            
        Returns:
            Processed calendar data with summary
        """
        if not events:
            return self._empty_calendar_response(working_hours)
        
        # Use provided working hours or defaults
        work_start, work_end = working_hours or (self.default_work_start, self.default_work_end)
        
        # Process each event
        processed_meetings = []
        total_meeting_minutes = 0
        meeting_blocks = []
        
        for event in events:
            if event.get('isCancelled', False):
                continue
                
            meeting_info = self._extract_meeting_info(event)
            processed_meetings.append(meeting_info)
            
            # Calculate duration
            duration = meeting_info['duration_minutes']
            total_meeting_minutes += duration
            
            # Store time blocks for focus time calculation
            meeting_blocks.append({
                'start': meeting_info['start_datetime'],
                'end': meeting_info['end_datetime'],
                'duration': duration
            })
        
        # Sort meetings by start time
        processed_meetings.sort(key=lambda x: x['start_datetime'])
        
        # Calculate metrics
        total_meeting_hours = round(total_meeting_minutes / 60, 1)
        focus_time_hours = self._calculate_focus_time(meeting_blocks, work_start, work_end)
        
        # Generate summaries
        meeting_summary = self._generate_meeting_summary(len(processed_meetings), total_meeting_hours)
        focus_summary = self._generate_focus_summary(focus_time_hours)
        
        # Analyze meeting patterns
        patterns = self._analyze_meeting_patterns(processed_meetings)
        
        return {
            'meetings': processed_meetings,
            'total_meetings': len(processed_meetings),
            'total_meeting_hours': total_meeting_hours,
            'focus_time_hours': focus_time_hours,
            'summary': meeting_summary,
            'focus_summary': focus_summary,
            'meeting_blocks': meeting_blocks,
            'patterns': patterns,
            'busiest_hours': self._find_busiest_hours(meeting_blocks)
        }
    
    def _empty_calendar_response(self, working_hours: Tuple[int, int] = None) -> Dict[str, Any]:
        """Return response for empty calendar"""
        work_start, work_end = working_hours or (self.default_work_start, self.default_work_end)
        work_hours = work_end - work_start
        
        return {
            'meetings': [],
            'total_meetings': 0,
            'total_meeting_hours': 0,
            'focus_time_hours': work_hours,
            'summary': "You have no meetings scheduled for today.",
            'focus_summary': f"Your entire {work_hours}-hour work day is available for focused work.",
            'meeting_blocks': [],
            'patterns': {},
            'busiest_hours': []
        }
    
    def _extract_meeting_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format meeting information"""
        # Parse datetime strings
        start_dt = self._parse_datetime(event['start']['dateTime'])
        end_dt = self._parse_datetime(event['end']['dateTime'])
        
        # Format display time
        time_str = start_dt.strftime('%-I:%M %p')
        if end_dt.date() == start_dt.date():
            time_str += f" - {end_dt.strftime('%-I:%M %p')}"
        
        # Extract organizer
        organizer_info = event.get('organizer', {})
        organizer_email = organizer_info.get('emailAddress', {})
        organizer = organizer_email.get('name') or organizer_email.get('address', 'Unknown')
        
        # Extract location
        location = event.get('location', {})
        location_str = location.get('displayName', '')
        
        # Check if online meeting
        is_online = bool(event.get('onlineMeeting')) or 'teams' in location_str.lower()
        
        # Extract agenda/body
        body = event.get('body', {})
        agenda = None
        if body and body.get('content'):
            content = body['content']
            # Clean HTML if present
            if body.get('contentType') == 'html':
                import re
                content = re.sub('<.*?>', '', content)
            agenda = content[:200].strip()
            if len(content) > 200:
                agenda += '...'
        
        # Extract attendees count
        attendees = event.get('attendees', [])
        required_attendees = [a for a in attendees if a.get('type') == 'required']
        
        # Calculate duration
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        
        return {
            'id': event.get('id'),
            'subject': event.get('subject', 'No Subject'),
            'time': time_str,
            'start_datetime': start_dt,
            'end_datetime': end_dt,
            'duration_minutes': duration_minutes,
            'duration_hours': round(duration_minutes / 60, 1),
            'organizer': organizer,
            'location': location_str or ('Online Meeting' if is_online else 'No location specified'),
            'is_online': is_online,
            'agenda': agenda,
            'attendee_count': len(attendees),
            'required_attendee_count': len(required_attendees),
            'show_as': event.get('showAs', 'busy'),
            'is_all_day': event.get('isAllDay', False),
            'importance': event.get('importance', 'normal')
        }
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse Graph API datetime string"""
        try:
            # Handle different datetime formats
            if datetime_str.endswith('Z'):
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(datetime_str)
            
            # Convert to timezone-naive for consistent comparison
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            
            return dt
        except Exception as e:
            # Fallback to current time if parsing fails
            return datetime.now()
    
    def _calculate_focus_time(self, meeting_blocks: List[Dict], 
                            work_start: int, work_end: int) -> float:
        """Calculate available focus time during working hours"""
        if not meeting_blocks:
            return work_end - work_start
        
        # Create working day timeline
        now = datetime.now()
        work_start_dt = now.replace(hour=work_start, minute=0, second=0, microsecond=0)
        work_end_dt = now.replace(hour=work_end, minute=0, second=0, microsecond=0)
        
        # Calculate total working minutes
        total_work_minutes = (work_end - work_start) * 60
        
        # Calculate meeting minutes during working hours
        meeting_minutes_in_work_hours = 0
        
        for block in meeting_blocks:
            # Only count meetings during working hours
            meeting_start = max(block['start'], work_start_dt)
            meeting_end = min(block['end'], work_end_dt)
            
            if meeting_start < meeting_end:
                duration = (meeting_end - meeting_start).total_seconds() / 60
                meeting_minutes_in_work_hours += duration
        
        # Calculate focus time
        focus_minutes = max(0, total_work_minutes - meeting_minutes_in_work_hours)
        return round(focus_minutes / 60, 1)
    
    def _generate_meeting_summary(self, meeting_count: int, total_hours: float) -> str:
        """Generate meeting summary text"""
        if meeting_count == 0:
            return "You have no meetings scheduled for today."
        elif meeting_count == 1:
            return f"You have 1 meeting today ({total_hours} hours)."
        else:
            return f"You have {meeting_count} meetings today ({total_hours} hours total)."
    
    def _generate_focus_summary(self, focus_hours: float) -> str:
        """Generate focus time summary text"""
        if focus_hours <= 0:
            return "Your day is fully booked with meetings."
        elif focus_hours < 1:
            minutes = int(focus_hours * 60)
            return f"You have {minutes} minutes of focus time available between meetings."
        elif focus_hours == 1:
            return "You have 1 hour of dedicated focus time scheduled."
        else:
            return f"You have {focus_hours} hours of dedicated focus time scheduled."
    
    def _analyze_meeting_patterns(self, meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in meetings"""
        if not meetings:
            return {}
        
        patterns = {
            'back_to_back_count': 0,
            'online_meetings': 0,
            'in_person_meetings': 0,
            'recurring_topics': {},
            'average_duration': 0,
            'longest_meeting': None,
            'shortest_meeting': None
        }
        
        total_duration = 0
        
        for i, meeting in enumerate(meetings):
            # Count online vs in-person
            if meeting['is_online']:
                patterns['online_meetings'] += 1
            else:
                patterns['in_person_meetings'] += 1
            
            # Track duration
            duration = meeting['duration_minutes']
            total_duration += duration
            
            if not patterns['longest_meeting'] or duration > patterns['longest_meeting']['duration']:
                patterns['longest_meeting'] = {
                    'subject': meeting['subject'],
                    'duration': duration
                }
            
            if not patterns['shortest_meeting'] or duration < patterns['shortest_meeting']['duration']:
                patterns['shortest_meeting'] = {
                    'subject': meeting['subject'],
                    'duration': duration
                }
            
            # Check for back-to-back meetings
            if i > 0:
                prev_meeting = meetings[i-1]
                time_between = (meeting['start_datetime'] - prev_meeting['end_datetime']).total_seconds() / 60
                if time_between <= 5:  # 5 minutes or less between meetings
                    patterns['back_to_back_count'] += 1
        
        patterns['average_duration'] = round(total_duration / len(meetings)) if meetings else 0
        
        return patterns
    
    def _find_busiest_hours(self, meeting_blocks: List[Dict]) -> List[int]:
        """Find the busiest hours of the day"""
        hour_counts = {}
        
        for block in meeting_blocks:
            start_hour = block['start'].hour
            end_hour = block['end'].hour
            
            for hour in range(start_hour, end_hour + 1):
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if not hour_counts:
            return []
        
        # Sort hours by meeting count
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 3 busiest hours
        return [hour for hour, count in sorted_hours[:3]]
