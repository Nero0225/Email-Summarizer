"""
Structured Digest Generator

This module generates the 5-section structured digest as specified in the PRD:
1. Snapshot
2. Calendar breakdown
3. Email topics
4. Actions
5. Quick creates
"""
from datetime import datetime
from typing import Dict, List, Any
from app.services.framework_4d import Action4D


class StructuredDigestGenerator:
    """Generator for PRD-compliant structured digests"""
    
    def generate_digest(self, 
                       conversations: Dict[str, Any], 
                       calendar_data: Dict[str, Any],
                       user_name: str = "User") -> Dict[str, Any]:
        """
        Generate complete structured digest per PRD format
        
        Args:
            conversations: Processed email conversations
            calendar_data: Processed calendar data
            user_name: User's name for personalization
            
        Returns:
            Structured digest dictionary
        """
        # Convert conversations dict to list for easier processing
        conv_list = list(conversations.values())
        
        # Sort by importance and recency
        conv_list.sort(
            key=lambda x: (
                self._get_importance_score(x),
                x.get('latest_date', '')
            ),
            reverse=True
        )
        
        # Generate each section
        snapshot = self._generate_snapshot(conv_list, calendar_data)
        calendar_breakdown = self._generate_calendar_breakdown(calendar_data)
        email_topics = self._generate_email_topics(conv_list)
        actions = self._generate_actions_section(conv_list)
        quick_creates = self._generate_quick_creates(conv_list)
        
        # Calculate metadata
        total_emails = sum(conv.get('email_count', 0) for conv in conv_list)
        
        # Combine into structured digest
        digest = {
            'title': 'Your Daily Digest',
            'generated_at': datetime.now().isoformat(),
            'user_name': user_name,
            'sections': {
                'snapshot': snapshot,
                'calendar_breakdown': calendar_breakdown,
                'email_topics': email_topics,
                'actions': actions,
                'quick_creates': quick_creates
            },
            'metadata': {
                'total_conversations': len(conv_list),
                'total_emails': total_emails,
                'total_meetings': calendar_data.get('total_meetings', 0),
                'meeting_hours': calendar_data.get('total_meeting_hours', 0),
                'focus_hours': calendar_data.get('focus_time_hours', 0)
            }
        }
        
        return digest
    
    def _get_importance_score(self, conversation: Dict[str, Any]) -> float:
        """Calculate importance score for conversation"""
        score = 0.0
        
        # Classification confidence
        classification = conversation.get('classification', {})
        confidence = classification.get('confidence', 0)
        action = classification.get('action')
        
        # Weight by action type
        if action == Action4D.DO:
            score += confidence * 3.0
        elif action == Action4D.DELEGATE:
            score += confidence * 2.0
        elif action == Action4D.DEFER:
            score += confidence * 1.5
        else:
            score += confidence * 0.5
        
        # Email count factor
        email_count = conversation.get('email_count', 1)
        score += min(email_count / 10.0, 1.0)
        
        # Importance level
        if conversation.get('importance') == 'high':
            score += 2.0
        elif conversation.get('importance') == 'normal':
            score += 1.0
        
        return score
    
    def _generate_snapshot(self, conversations: List[Dict[str, Any]], 
                          calendar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate snapshot section per PRD format:
        - X unread emails since last check
        - X meetings today (X hours total)  
        - Suggested actions: X items flagged
        """
        total_emails = sum(conv.get('email_count', 0) for conv in conversations)
        meeting_count = calendar_data.get('total_meetings', 0)
        meeting_hours = calendar_data.get('total_meeting_hours', 0)
        
        # Count high-priority actions (Do + Delegate)
        high_priority_actions = 0
        for conv in conversations:
            action = conv.get('classification', {}).get('action')
            if action in [Action4D.DO, Action4D.DELEGATE]:
                high_priority_actions += 1
        
        # Format summary bullets
        bullets = []
        bullets.append(f"{total_emails} unread emails since you last checked")
        
        if meeting_count == 0:
            bullets.append("No meetings scheduled today")
        elif meeting_count == 1:
            bullets.append(f"1 meeting today ({meeting_hours} hours)")
        else:
            bullets.append(f"{meeting_count} meetings today ({meeting_hours} hours total)")
        
        bullets.append(f"Suggested actions: {high_priority_actions} items flagged")
        
        return {
            'unread_emails': total_emails,
            'meetings_today': meeting_count,
            'meeting_hours': meeting_hours,
            'flagged_actions': high_priority_actions,
            'summary_bullets': bullets,
            'summary_text': '\n• '.join([''] + bullets)  # Add bullet to first item
        }
    
    def _generate_calendar_breakdown(self, calendar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate calendar breakdown per PRD format:
        - List of meetings with who, when, agenda
        - Meeting hours summary
        - Focus time indication
        """
        meetings = calendar_data.get('meetings', [])
        
        formatted_meetings = []
        for i, meeting in enumerate(meetings, 1):
            formatted_meeting = {
                'number': i,
                'time': meeting.get('time', 'Time TBD'),
                'subject': meeting.get('subject', 'No Subject'),
                'organizer': meeting.get('organizer', 'Unknown'),
                'location': meeting.get('location', ''),
                'duration': f"{meeting.get('duration_hours', 0)} hours",
                'attendees': meeting.get('attendee_count', 0),
                'is_online': meeting.get('is_online', False)
            }
            
            # Add agenda if available
            if meeting.get('agenda'):
                formatted_meeting['agenda'] = meeting['agenda'][:150] + '...' if len(meeting.get('agenda', '')) > 150 else meeting.get('agenda')
            else:
                formatted_meeting['agenda'] = 'No agenda provided'
            
            formatted_meetings.append(formatted_meeting)
        
        return {
            'meetings': formatted_meetings,
            'summary': calendar_data.get('summary', 'No meetings scheduled'),
            'focus_summary': calendar_data.get('focus_summary', 'Full day available for focus work'),
            'total_hours': calendar_data.get('total_meeting_hours', 0),
            'focus_hours': calendar_data.get('focus_time_hours', 8),
            'patterns': calendar_data.get('patterns', {}),
            'busiest_hours': calendar_data.get('busiest_hours', [])
        }
    
    def _generate_email_topics(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate email topics section per PRD format:
        - Grouped by conversation
        - Subject + purpose + recommended action
        """
        topics = []
        
        # Take top conversations (limit for readability)
        for i, conv in enumerate(conversations[:15], 1):
            # Extract key information
            latest_sender = conv.get('latest_sender', {})
            sender_name = latest_sender.get('name', 'Unknown') if isinstance(latest_sender, dict) else str(latest_sender)
            
            # Get classification info
            classification = conv.get('classification', {})
            action = classification.get('action', Action4D.DELETE)
            reason = classification.get('reason', '')
            confidence = classification.get('confidence', 0)
            
            # Format action recommendation
            action_text = self._format_action_recommendation(action, reason, confidence)
            
            topic = {
                'number': i,
                'subject': conv.get('subject', 'No Subject'),
                'email_count': conv.get('email_count', 1),
                'latest_sender': sender_name,
                'summary': conv.get('summary', 'No summary available'),
                'action': action_text,
                'confidence': confidence,
                'has_attachments': conv.get('has_attachments', False),
                'importance': conv.get('importance', 'normal')
            }
            
            topics.append(topic)
        
        return {
            'topics': topics,
            'total_conversations': len(conversations),
            'shown_conversations': len(topics)
        }
    
    def _generate_actions_section(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate actions section per PRD format:
        - Organized by 4D framework
        - Specific recommendations
        """
        # Group by 4D category
        actions_by_type = {
            'Do': [],
            'Delegate': [],
            'Defer': [],
            'Delete': []
        }
        
        for conv in conversations:
            classification = conv.get('classification', {})
            action = classification.get('action', Action4D.DELETE)
            confidence = classification.get('confidence', 0)
            
            action_name = action.value if isinstance(action, Action4D) else str(action)
            
            if action_name in actions_by_type:
                actions_by_type[action_name].append({
                    'subject': conv.get('subject', 'No Subject'),
                    'reason': classification.get('reason', ''),
                    'confidence': confidence,
                    'sender': conv.get('latest_sender', {}).get('name', 'Unknown') if isinstance(conv.get('latest_sender'), dict) else 'Unknown'
                })
        
        # Sort each category by confidence
        for action_type in actions_by_type:
            actions_by_type[action_type].sort(key=lambda x: x['confidence'], reverse=True)
        
        # Generate specific recommendations
        recommendations = self._generate_specific_recommendations(actions_by_type)
        
        # Calculate totals
        total_actions = sum(len(items) for action, items in actions_by_type.items() if action != 'Delete')
        
        return {
            'by_category': actions_by_type,
            'recommendations': recommendations,
            'total_actions': total_actions,
            'priority_matrix': self._create_priority_matrix(actions_by_type)
        }
    
    def _generate_quick_creates(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate quick creates section per PRD format:
        - List of suggested actions
        - No integration yet (MVP limitation)
        """
        quick_actions = []
        
        # Get high-priority conversations
        do_items = [conv for conv in conversations if conv.get('classification', {}).get('action') == Action4D.DO]
        delegate_items = [conv for conv in conversations if conv.get('classification', {}).get('action') == Action4D.DELEGATE]
        defer_items = [conv for conv in conversations if conv.get('classification', {}).get('action') == Action4D.DEFER]
        
        # Add quick actions for Do items
        for item in do_items[:3]:
            quick_actions.append({
                'id': f"do_{len(quick_actions)}",
                'type': 'task',
                'description': f"Review and respond: {item.get('subject', 'No Subject')}",
                'priority': 'high',
                'source': 'email',
                'metadata': {
                    'email_count': item.get('email_count', 1),
                    'sender': item.get('latest_sender', {}).get('name', 'Unknown') if isinstance(item.get('latest_sender'), dict) else 'Unknown'
                }
            })
        
        # Add quick actions for Delegate items
        for item in delegate_items[:2]:
            quick_actions.append({
                'id': f"delegate_{len(quick_actions)}",
                'type': 'delegation',
                'description': f"Assign to team member: {item.get('subject', 'No Subject')}",
                'priority': 'medium',
                'source': 'email',
                'metadata': {
                    'suggested_assignee': 'Team member with relevant expertise'
                }
            })
        
        # Add quick actions for Defer items
        for item in defer_items[:2]:
            quick_actions.append({
                'id': f"defer_{len(quick_actions)}",
                'type': 'calendar',
                'description': f"Schedule meeting for: {item.get('subject', 'No Subject')}",
                'priority': 'low',
                'source': 'email',
                'metadata': {
                    'suggested_duration': '30 minutes',
                    'suggested_timeframe': 'Next week'
                }
            })
        
        return {
            'suggested_actions': quick_actions,
            'total_suggestions': len(quick_actions),
            'note': 'Quick create actions - Manual creation required (no integration in MVP)',
            'integration_status': 'planned_for_future'
        }
    
    def _format_action_recommendation(self, action: Action4D, reason: str, confidence: float) -> str:
        """Format action recommendation text"""
        action_text = action.value if isinstance(action, Action4D) else str(action)
        
        # Add confidence indicator
        if confidence > 0.7:
            confidence_text = " (High confidence)"
        elif confidence > 0.4:
            confidence_text = " (Medium confidence)"
        else:
            confidence_text = " (Low confidence)"
        
        if reason and reason != "No reason provided":
            return f"Action: {action_text} - {reason}{confidence_text}"
        else:
            return f"Action: {action_text}{confidence_text}"
    
    def _generate_specific_recommendations(self, actions_by_type: Dict[str, List]) -> List[str]:
        """Generate specific actionable recommendations"""
        recommendations = []
        
        # DO recommendations (highest priority)
        do_items = actions_by_type.get('Do', [])
        for item in do_items[:3]:
            if item['confidence'] > 0.6:
                recommendations.append(f'<i class="fas fa-circle text-danger"></i> Do (Today): {item["subject"]}')
        
        # DELEGATE recommendations
        delegate_items = actions_by_type.get('Delegate', [])
        for item in delegate_items[:2]:
            recommendations.append(f'<i class="fas fa-circle text-warning"></i> Delegate: {item["subject"]} → Assign to appropriate team member')
        
        # DEFER recommendations
        defer_items = actions_by_type.get('Defer', [])
        for item in defer_items[:2]:
            recommendations.append(f'<i class="fas fa-circle text-success"></i> Defer: Schedule time next week for {item["subject"]}')
        
        # DELETE summary
        delete_count = len(actions_by_type.get('Delete', []))
        if delete_count > 5:
            recommendations.append(f'<i class="fas fa-trash-alt text-secondary"></i> Delete: Archive {delete_count} informational/promotional emails')
        
        # Decision required items
        decision_items = [
            item for item in do_items + delegate_items 
            if 'decision' in item.get('subject', '').lower() or 'decide' in item.get('reason', '').lower()
        ]
        for item in decision_items[:2]:
            recommendations.append(f'<i class="fas fa-bolt text-warning"></i> Decision Required: {item["subject"]}')
        
        return recommendations
    
    def _create_priority_matrix(self, actions_by_type: Dict[str, List]) -> Dict[str, Any]:
        """Create a priority matrix for actions"""
        return {
            'urgent_important': len([item for item in actions_by_type.get('Do', []) if item['confidence'] > 0.6]),
            'not_urgent_important': len(actions_by_type.get('Defer', [])),
            'urgent_not_important': len(actions_by_type.get('Delegate', [])),
            'not_urgent_not_important': len(actions_by_type.get('Delete', []))
        }
    
    def format_digest_html(self, digest: Dict[str, Any]) -> str:
        """Format digest as HTML for display"""
        sections = digest['sections']
        metadata = digest['metadata']
        
        # Generate formatted timestamp
        generated_time = datetime.fromisoformat(digest['generated_at']).strftime('%B %d, %Y at %I:%M %p')
        
        html_parts = [
            f'<div class="daily-digest">',
            f'<h1>{digest["title"]}</h1>',
            f'<p class="generated-time">Generated on {generated_time}</p>',
            '',
            self._format_snapshot_html(sections['snapshot']),
            self._format_calendar_html(sections['calendar_breakdown']),
            self._format_email_topics_html(sections['email_topics']),
            self._format_actions_html(sections['actions']),
            self._format_quick_creates_html(sections['quick_creates']),
            '</div>'
        ]
        
        return '\n'.join(html_parts)
    
    def _format_snapshot_html(self, snapshot: Dict[str, Any]) -> str:
        """Format snapshot section as HTML"""
        return f'''
        <section class="snapshot">
            <h2><i class="fas fa-chart-bar"></i> Snapshot</h2>
            <div class="snapshot-content">
                {snapshot['summary_text'].replace(chr(10), '<br>')}
            </div>
        </section>
        '''
    
    def _format_calendar_html(self, calendar: Dict[str, Any]) -> str:
        """Format calendar section as HTML"""
        meetings_html = []
        for meeting in calendar['meetings']:
            location = f" @ {meeting['location']}" if meeting['location'] else ""
            online_badge = ' <span class="badge online">Online</span>' if meeting['is_online'] else ''
            
            meetings_html.append(f'''
            <div class="calendar-event">
                <h4>{meeting['number']}. {meeting['time']} – {meeting['subject']}{online_badge}</h4>
                <p class="event-details">
                    <span><i class="fas fa-user"></i> Organizer: {meeting['organizer']}</span>
                    <span><i class="fas fa-clock"></i> Duration: {meeting['duration']}</span>
                    <span><i class="fas fa-users"></i> Attendees: {meeting['attendees']}</span>
                </p>
                <p class="event-agenda"><i class="fas fa-file-alt"></i> {meeting['agenda']}</p>
                {f'<p class="event-location"><i class="fas fa-map-marker-alt"></i> {location}</p>' if location else ''}
            </div>
            ''')
        
        return f'''
        <section class="calendar-breakdown">
            <h2><i class="fas fa-calendar-day"></i> Today\'s Calendar</h2>
            <div class="calendar-summary">
                <p>{calendar['summary']}</p>
                <p class="focus-time">{calendar['focus_summary']}</p>
            </div>
            <div class="meetings-list">
                {''.join(meetings_html) if meetings_html else '<p>No meetings scheduled today.</p>'}
            </div>
        </section>
        '''
    
    def _format_email_topics_html(self, topics_data: Dict[str, Any]) -> str:
        """Format email topics as HTML"""
        topics_html = []
        for topic in topics_data['topics'][:10]:  # Limit display
            importance_badge = ''
            if topic['importance'] == 'high':
                importance_badge = ' <span class="badge high-importance">High Priority</span>'
            
            attachments_badge = ' <i class="fas fa-paperclip"></i>' if topic['has_attachments'] else ''
            
            topics_html.append(f'''
            <div class="email-topic">
                <h3>{topic['number']}. {topic['subject']}{importance_badge}{attachments_badge}</h3>
                <p class="topic-meta">
                    <span>{topic['email_count']} email{"s" if topic['email_count'] > 1 else ""} in thread</span>
                    <span>Latest from: {topic['latest_sender']}</span>
                </p>
                <p class="topic-summary">{topic['summary']}</p>
                <p class="topic-action">{topic['action']}</p>
            </div>
            ''')
        
        return f'''
        <section class="email-topics">
            <h2><i class="fas fa-envelope"></i> Email Summary</h2>
            <p class="section-meta">Showing {len(topics_data['topics'])} of {topics_data['total_conversations']} conversations</p>
            <div class="topics-list">
                {''.join(topics_html)}
            </div>
        </section>
        '''
    
    def _format_actions_html(self, actions_data: Dict[str, Any]) -> str:
        """Format actions section as HTML"""
        recommendations_html = ''.join([f'<li>{rec}</li>' for rec in actions_data['recommendations']])
        
        return f'''
        <section class="recommended-actions">
            <h2><i class="fas fa-bolt"></i> Recommended Actions</h2>
            <p class="action-summary">Total actionable items: {actions_data['total_actions']}</p>
            <ul class="action-list">
                {recommendations_html}
            </ul>
        </section>
        '''
    
    def _format_quick_creates_html(self, quick_creates: Dict[str, Any]) -> str:
        """Format quick creates section as HTML"""
        if not quick_creates['suggested_actions']:
            return ''
        
        actions_html = []
        for action in quick_creates['suggested_actions']:
            icon_class = {'task': 'fa-edit', 'delegation': 'fa-users', 'calendar': 'fa-calendar'}.get(action['type'], 'fa-thumbtack')
            actions_html.append(f'''
            <div class="quick-action {action['type']}">
                <span class="action-icon"><i class="fas {icon_class}"></i></span>
                <span class="action-text">{action['description']}</span>
                <span class="action-priority priority-{action['priority']}">{action['priority'].title()}</span>
            </div>
            ''')
        
        return f'''
        <section class="quick-creates">
            <h2><i class="fas fa-bolt"></i> Quick Actions</h2>
            <p class="section-note">{quick_creates['note']}</p>
            <div class="actions-grid">
                {''.join(actions_html)}
            </div>
        </section>
        '''
