"""
Email Service

This module handles email processing, conversation grouping,
and 4D classification.
"""
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from flask import current_app
from app.services.framework_4d import Framework4DClassifier, Action4D


class EmailService:
    """Service class for email processing operations"""
    
    def __init__(self):
        self.classifier = Framework4DClassifier()
    
    def process_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process emails: group by conversation and classify
        
        Implements:
            - ConversationId-based threading
            - Processing of Inbox-only emails (Junk/Clutter excluded at fetch level)
            - Handles up to 200 emails (cap enforced at fetch level)
        
        Args:
            emails: List of email dictionaries from Graph API
            
        Returns:
            Dictionary of processed conversations
        """
        # Group emails by conversation
        conversations = self._group_by_conversation(emails)
        current_app.logger.info(f"Grouped {len(emails)} emails into {len(conversations)} conversations")
        
        # Process each conversation
        processed_conversations = {}
        
        for conv_id, conv_emails in conversations.items():
            # Sort emails by date (newest first)
            conv_emails.sort(
                key=lambda x: x.get('receivedDateTime', ''),
                reverse=True
            )
            
            # Get conversation metadata
            latest_email = conv_emails[0]
            
            # Classify conversation using 4D framework
            action, reason, confidence = self.classifier.classify_conversation(conv_emails)
            
            processed_conversations[conv_id] = {
                'conversation_id': conv_id,
                'emails': conv_emails,
                'email_count': len(conv_emails),
                'subject': latest_email.get('subject', 'No Subject'),
                'latest_sender': self._extract_sender(latest_email),
                'latest_date': latest_email.get('receivedDateTime', ''),
                'first_date': conv_emails[-1].get('receivedDateTime', ''),
                'has_attachments': any(e.get('hasAttachments', False) for e in conv_emails),
                'importance': self._get_max_importance(conv_emails),
                'classification': {
                    'action': action,
                    'reason': reason,
                    'confidence': confidence
                },
                'summary': self._generate_conversation_summary(conv_emails)
            }
        
        return processed_conversations
    
    def _group_by_conversation(self, emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group emails by conversation ID"""
        conversations = defaultdict(list)
        
        for email in emails:
            conv_id = email.get('conversationId')
            if conv_id:
                conversations[conv_id].append(email)
            else:
                # Fallback: use email ID as conversation ID
                conversations[email.get('id', 'unknown')].append(email)
        
        return dict(conversations)
    
    def _extract_sender(self, email: Dict[str, Any]) -> Dict[str, str]:
        """Extract sender information from email"""
        from_field = email.get('from', {})
        if isinstance(from_field, dict):
            email_address = from_field.get('emailAddress', {})
            return {
                'name': email_address.get('name', 'Unknown'),
                'email': email_address.get('address', 'unknown@example.com')
            }
        return {'name': 'Unknown', 'email': 'unknown@example.com'}
    
    def _get_max_importance(self, emails: List[Dict[str, Any]]) -> str:
        """Get maximum importance level from email thread"""
        importance_levels = ['low', 'normal', 'high']
        max_importance = 'normal'
        max_index = 1
        
        for email in emails:
            importance = email.get('importance', 'normal').lower()
            if importance in importance_levels:
                index = importance_levels.index(importance)
                if index > max_index:
                    max_index = index
                    max_importance = importance
        
        return max_importance
    
    def _generate_conversation_summary(self, emails: List[Dict[str, Any]]) -> str:
        """
        Generate a brief summary of the conversation
        
        Args:
            emails: List of emails in conversation
            
        Returns:
            Summary string
        """
        if not emails:
            return "Empty conversation"
        
        # Get key information
        latest_email = emails[0]
        subject = latest_email.get('subject', 'No Subject')
        sender = self._extract_sender(latest_email)
        email_count = len(emails)
        
        # Extract key points from body preview
        body_preview = latest_email.get('bodyPreview', '') or ''
        key_point = self._extract_key_point(body_preview)
        
        # Build summary
        if email_count == 1:
            summary = f"Email from {sender['name']} about {subject}"
        else:
            summary = f"Conversation ({email_count} emails) about {subject} with {sender['name']}"
        
        if key_point:
            summary += f". {key_point}"
        
        return summary
    
    def _extract_key_point(self, body_preview: str) -> str:
        """Extract key point from email body preview"""
        if not body_preview:
            return ""
        
        # Clean and truncate
        body = body_preview.strip()
        
        # Look for question marks (likely questions needing answers)
        if '?' in body:
            # Find the sentence with the question
            sentences = body.split('.')
            for sentence in sentences:
                if '?' in sentence:
                    return sentence.strip()[:100] + ('...' if len(sentence) > 100 else '')
        
        # Look for action phrases
        action_phrases = [
            'please', 'could you', 'can you', 'need', 'require',
            'urgent', 'asap', 'deadline', 'due'
        ]
        
        body_lower = body.lower()
        for phrase in action_phrases:
            if phrase in body_lower:
                # Find the sentence containing the action phrase
                sentences = body.split('.')
                for sentence in sentences:
                    if phrase in sentence.lower():
                        return sentence.strip()[:100] + ('...' if len(sentence) > 100 else '')
        
        # Default: return first sentence or portion
        first_sentence = body.split('.')[0]
        if len(first_sentence) > 100:
            return first_sentence[:100] + '...'
        return first_sentence
    
    def get_email_statistics(self, conversations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get statistics about processed emails
        
        Args:
            conversations: Processed conversations dictionary
            
        Returns:
            Statistics dictionary
        """
        total_emails = sum(conv['email_count'] for conv in conversations.values())
        
        # Count by classification
        action_counts = defaultdict(int)
        for conv in conversations.values():
            action = conv['classification']['action']
            if isinstance(action, Action4D):
                action_counts[action.value] += 1
            else:
                action_counts[str(action)] += 1
        
        # Count by importance
        importance_counts = defaultdict(int)
        for conv in conversations.values():
            importance_counts[conv['importance']] += 1
        
        return {
            'total_conversations': len(conversations),
            'total_emails': total_emails,
            'avg_emails_per_conversation': round(total_emails / max(len(conversations), 1), 1),
            'classification_counts': dict(action_counts),
            'importance_counts': dict(importance_counts),
            'conversations_with_attachments': sum(
                1 for conv in conversations.values() if conv['has_attachments']
            )
        }
