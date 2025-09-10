"""
4D Framework Classifier

This module implements the 4D (Do, Delegate, Defer, Delete) framework
for email classification as specified in the PRD.
"""
import re
from typing import Dict, List, Any, Tuple
from enum import Enum


class Action4D(Enum):
    """4D Framework actions"""
    DO = "Do"
    DELEGATE = "Delegate"
    DEFER = "Defer"
    DELETE = "Delete"


class Framework4DClassifier:
    """Classifier for 4D framework email categorization"""
    
    def __init__(self):
        # PRD-specified keyword triggers for 4D classification
        self.classification_rules = {
            Action4D.DO: {
                'keywords': [
                    'please reply', 'urgent', 'asap', 'immediate', 'today', 'now',
                    'review and approve', 'sign off', 'confirm', 'approve',
                    'deadline today', 'due today', 'expires today', 'final',
                    'action required', 'your input needed', 'please respond',
                    'critical', 'high priority', 'time sensitive', 'eod',
                    'end of day', 'by close of business', 'cob'
                ],
                'patterns': [
                    r'please\s+reply\s+by',
                    r'need\s+your\s+approval',
                    r'waiting\s+for\s+you',
                    r'can\s+you\s+please',
                    r'urgent.*action',
                    r'deadline.*today',
                    r'respond\s+by\s+\d+',
                    r'due\s+(?:by|on)\s+today',
                    r'complete\s+by\s+\w+day'
                ],
                'weight': 1.5  # Higher weight for DO actions
            },
            Action4D.DELEGATE: {
                'keywords': [
                    'can you handle', 'please assign', 'delegate to',
                    'forward to', 'pass to', 'assign to team',
                    'someone else', 'team member', 'subordinate',
                    'assign this to', 'hand over to', 'reassign',
                    'find someone', 'who can help', 'not my area'
                ],
                'patterns': [
                    r'can\s+someone\s+else',
                    r'assign\s+to\s+\w+',
                    r'delegate\s+this',
                    r'forward\s+to\s+\w+',
                    r'pass\s+this\s+to',
                    r'have\s+\w+\s+handle',
                    r'ask\s+\w+\s+to\s+do'
                ],
                'weight': 1.2
            },
            Action4D.DEFER: {
                'keywords': [
                    'schedule', 'plan for', 'next week', 'next month',
                    'later', 'future', 'postpone', 'reschedule',
                    'book meeting', 'set up meeting', 'plan discussion',
                    'follow up', 'circle back', 'revisit', 'touch base',
                    'when you have time', 'no rush', 'whenever possible'
                ],
                'patterns': [
                    r'schedule.*meeting',
                    r'plan.*for.*next',
                    r'follow.*up.*next',
                    r'revisit.*next',
                    r'discuss.*next',
                    r'meeting.*to.*discuss',
                    r'let\'s\s+meet',
                    r'can\s+we\s+schedule',
                    r'available\s+next\s+\w+'
                ],
                'weight': 1.0
            },
            Action4D.DELETE: {
                'keywords': [
                    'newsletter', 'unsubscribe', 'promotional', 'marketing',
                    'advertisement', 'spam', 'no action required',
                    'fyi only', 'for your information', 'informational',
                    'auto-generated', 'automated', 'notification only',
                    'no reply', 'do not reply', 'announcement',
                    'update only', 'status update', 'weekly digest'
                ],
                'patterns': [
                    r'newsletter.*subscription',
                    r'promotional.*email',
                    r'marketing.*campaign',
                    r'no.*action.*required',
                    r'fyi.*only',
                    r'automated.*message',
                    r'do\s+not\s+reply',
                    r'unsubscribe.*link',
                    r'sent\s+from.*automated'
                ],
                'weight': 0.8
            }
        }
        
        # Context modifiers that affect classification
        self.urgency_indicators = [
            'urgent', 'asap', 'immediately', 'critical', 'emergency',
            'high priority', 'time sensitive', 'deadline'
        ]
        
        self.delegation_indicators = [
            'fwd:', 'fw:', 'please handle', 'can you take care',
            'passing this to you', 'your expertise'
        ]
    
    def classify_email(self, email: Dict[str, Any]) -> Tuple[Action4D, str, float]:
        """
        Classify email using 4D framework
        
        Args:
            email: Email dictionary with subject, body, etc.
            
        Returns:
            Tuple of (Action, Reason, Confidence)
        """
        # Extract text content
        subject = email.get('subject', '').lower()
        body = self._get_email_body(email).lower()
        from_address = self._get_sender_address(email).lower()
        
        # Check for automated emails first
        if self._is_automated_email(subject, body, from_address):
            return Action4D.DELETE, "Automated/promotional email", 0.9
        
        combined_text = f"{subject} {body}"
        
        # Score each category
        scores = {}
        reasons = {}
        
        for action in Action4D:
            score, reason = self._calculate_score(combined_text, action)
            
            # Apply context modifiers
            if action == Action4D.DO and self._has_urgency_indicators(combined_text):
                score *= 1.5
                reason += " (urgent)"
            
            if action == Action4D.DELEGATE and self._has_delegation_indicators(subject):
                score *= 1.3
                reason += " (forwarded)"
            
            scores[action] = score
            reasons[action] = reason
        
        # Find highest scoring action
        best_action = max(scores.keys(), key=lambda x: scores[x])
        best_score = scores[best_action]
        best_reason = reasons[best_action]
        
        # Default to DO if no clear classification and has action indicators
        if best_score < 1.0:
            if self._has_action_indicators(combined_text):
                return Action4D.DO, "Contains action-oriented language", 0.4
            else:
                return Action4D.DELETE, "No clear action required", 0.5
        
        # Calculate confidence (normalize to 0.0-1.0)
        max_possible_score = 10.0  # Adjust based on testing
        confidence = min(best_score / max_possible_score, 1.0)
        
        return best_action, best_reason, confidence
    
    def classify_conversation(self, emails: List[Dict[str, Any]]) -> Tuple[Action4D, str, float]:
        """
        Classify entire conversation thread
        
        Per PRD: Use latest email in thread for classification
        
        Args:
            emails: List of emails in conversation
            
        Returns:
            Tuple of (Action, Reason, Confidence)
        """
        if not emails:
            return Action4D.DELETE, "Empty conversation", 0.0
        
        # Sort by date and get latest email
        sorted_emails = sorted(
            emails,
            key=lambda x: x.get('receivedDateTime', ''),
            reverse=True
        )
        
        latest_email = sorted_emails[0]
        
        # Classify based on latest email
        action, reason, confidence = self.classify_email(latest_email)
        
        # Adjust confidence based on thread length
        thread_factor = min(len(emails) / 10.0, 1.0)  # More emails = more important
        adjusted_confidence = confidence * (0.8 + 0.2 * thread_factor)
        
        return action, reason, adjusted_confidence
    
    def _calculate_score(self, text: str, action: Action4D) -> Tuple[float, str]:
        """Calculate score for a specific 4D action category"""
        rules = self.classification_rules[action]
        score = 0.0
        matched_keywords = []
        
        # Check keywords
        for keyword in rules['keywords']:
            if keyword in text:
                score += 1.0 * rules['weight']
                matched_keywords.append(keyword)
        
        # Check patterns
        for pattern in rules['patterns']:
            if re.search(pattern, text, re.IGNORECASE):
                score += 2.0 * rules['weight']  # Patterns get higher weight
                matched_keywords.append(f"pattern: {pattern[:20]}...")
        
        # Generate reason
        if matched_keywords:
            # Show first 3 matches
            reason = f"Matched: {', '.join(matched_keywords[:3])}"
            if len(matched_keywords) > 3:
                reason += f" (+{len(matched_keywords)-3} more)"
        else:
            reason = "No specific indicators found"
        
        return score, reason
    
    def _get_email_body(self, email: Dict[str, Any]) -> str:
        """Extract email body text"""
        # Try bodyPreview first
        body = email.get('bodyPreview', '') or ''
        
        # If no preview, try body content
        if not body and 'body' in email:
            body_data = email['body']
            if isinstance(body_data, dict):
                body = body_data.get('content', '')
            else:
                body = str(body_data)
        
        return body
    
    def _get_sender_address(self, email: Dict[str, Any]) -> str:
        """Extract sender email address"""
        from_field = email.get('from', {})
        if isinstance(from_field, dict) and 'emailAddress' in from_field:
            email_data = from_field['emailAddress']
            if isinstance(email_data, dict):
                return email_data.get('address', '')
        return ''
    
    def _is_automated_email(self, subject: str, body: str, from_address: str) -> bool:
        """Check if email is automated/promotional"""
        automated_indicators = [
            'noreply', 'no-reply', 'donotreply', 'automated',
            'notification@', 'newsletter@', 'marketing@',
            'unsubscribe', 'opt out', 'email preferences'
        ]
        
        for indicator in automated_indicators:
            if indicator in from_address or indicator in subject.lower():
                return True
        
        # Check for unsubscribe links in body
        if 'unsubscribe' in body and ('click here' in body or 'http' in body):
            return True
        
        return False
    
    def _has_urgency_indicators(self, text: str) -> bool:
        """Check if text contains urgency indicators"""
        return any(indicator in text for indicator in self.urgency_indicators)
    
    def _has_delegation_indicators(self, text: str) -> bool:
        """Check if text contains delegation indicators"""
        return any(indicator in text for indicator in self.delegation_indicators)
    
    def _has_action_indicators(self, text: str) -> bool:
        """Check if text has general action-oriented language"""
        action_words = [
            'please', 'need', 'required', 'request', 'can you',
            'would you', 'could you', 'action', 'task', 'complete',
            'finish', 'submit', 'send', 'provide', 'update', 'review'
        ]
        
        return any(word in text for word in action_words)
    
    def get_classification_statistics(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about classified conversations
        
        Args:
            conversations: List of classified conversations
            
        Returns:
            Statistics dictionary
        """
        action_counts = {action: 0 for action in Action4D}
        confidence_sum = {action: 0.0 for action in Action4D}
        high_confidence_items = []
        
        for conv in conversations:
            classification = conv.get('classification', {})
            action = classification.get('action')
            confidence = classification.get('confidence', 0)
            
            if isinstance(action, Action4D):
                action_counts[action] += 1
                confidence_sum[action] += confidence
                
                if confidence > 0.7:
                    high_confidence_items.append({
                        'subject': conv.get('subject'),
                        'action': action.value,
                        'confidence': confidence
                    })
        
        # Calculate averages
        avg_confidence = {}
        for action in Action4D:
            if action_counts[action] > 0:
                avg_confidence[action] = confidence_sum[action] / action_counts[action]
            else:
                avg_confidence[action] = 0.0
        
        return {
            'action_counts': {a.value: count for a, count in action_counts.items()},
            'average_confidence': {a.value: conf for a, conf in avg_confidence.items()},
            'high_confidence_items': high_confidence_items[:10],  # Top 10
            'total_classified': sum(action_counts.values())
        }
    
    def generate_action_recommendations(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """
        Generate actionable recommendations based on classifications
        
        Args:
            conversations: List of classified conversations
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Group by action type
        action_groups = {action: [] for action in Action4D}
        
        for conv in conversations:
            classification = conv.get('classification', {})
            action = classification.get('action')
            if isinstance(action, Action4D):
                action_groups[action].append(conv)
        
        # Generate recommendations for each type
        
        # DO items (highest priority)
        do_items = sorted(
            action_groups[Action4D.DO],
            key=lambda x: x.get('classification', {}).get('confidence', 0),
            reverse=True
        )
        for item in do_items[:3]:  # Top 3
            recommendations.append(f"Do (Today): {item.get('subject', 'No subject')}")
        
        # DELEGATE items
        for item in action_groups[Action4D.DELEGATE][:2]:  # Top 2
            subject = item.get('subject', 'No subject')
            recommendations.append(f"Delegate: {subject}")
        
        # DEFER items
        for item in action_groups[Action4D.DEFER][:2]:  # Top 2
            subject = item.get('subject', 'No subject')
            recommendations.append(f"Defer: Schedule time for {subject}")
        
        # DELETE summary
        delete_count = len(action_groups[Action4D.DELETE])
        if delete_count > 0:
            recommendations.append(f"Delete: Archive {delete_count} informational emails")
        
        return recommendations
