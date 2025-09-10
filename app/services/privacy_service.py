"""
Privacy Service

This module handles PII (Personally Identifiable Information) detection
and redaction for privacy protection.
"""
import re
import uuid
from typing import Dict, Tuple, Any, List
from flask import current_app


class PrivacyService:
    """Service class for privacy and PII redaction operations"""
    
    def __init__(self):
        # Regex patterns for common PII
        self.patterns = {
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'label': 'EMAIL'
            },
            'phone': {
                'pattern': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
                'label': 'PHONE'
            },
            'ssn': {
                'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
                'label': 'SSN'
            },
            'credit_card': {
                'pattern': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
                'label': 'CREDIT_CARD'
            },
            'ip_address': {
                'pattern': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                'label': 'IP_ADDRESS'
            },
            'url': {
                'pattern': r'https?://[^\s]+',
                'label': 'URL'
            },
            'date_of_birth': {
                'pattern': r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b',
                'label': 'DOB'
            },
            'postal_code': {
                'pattern': r'\b\d{5}(?:-\d{4})?\b',
                'label': 'POSTAL_CODE'
            }
        }
        
        # Company and project patterns
        self.entity_patterns = {
            'company': {
                'pattern': r'\b[A-Z][a-z]+\s+(?:Corp|Corporation|Inc|LLC|Ltd|Limited|Company|Co)\b',
                'label': 'COMPANY'
            },
            'project': {
                'pattern': r'\bProject\s+[A-Z][a-z]+\b',
                'label': 'PROJECT'
            }
        }
        
        # Common names pattern (simplified)
        self.name_indicators = ['Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Prof.']
    
    def redact_email(self, email_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Redact PII from email data
        
        Args:
            email_data: Email dictionary
            
        Returns:
            Tuple of (redacted_email, redaction_map)
        """
        redaction_map = {}
        redacted_email = email_data.copy()
        
        # Fields to redact
        text_fields = ['subject', 'bodyPreview', 'body']
        
        for field in text_fields:
            if field in email_data and email_data[field]:
                # Handle body field which might be a dict
                if field == 'body' and isinstance(email_data[field], dict):
                    body_content = email_data[field].get('content', '')
                    if body_content:
                        redacted_text, field_map = self._redact_text(body_content)
                        redacted_email[field] = email_data[field].copy()
                        redacted_email[field]['content'] = redacted_text
                        redaction_map.update(field_map)
                else:
                    redacted_text, field_map = self._redact_text(str(email_data[field]))
                    redacted_email[field] = redacted_text
                    redaction_map.update(field_map)
        
        # Redact sender information
        if 'from' in email_data:
            redacted_from, from_map = self._redact_sender(email_data['from'])
            redacted_email['from'] = redacted_from
            redaction_map.update(from_map)
        
        return redacted_email, redaction_map
    
    def _redact_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Redact PII from text
        
        Args:
            text: Text to redact
            
        Returns:
            Tuple of (redacted_text, redaction_map)
        """
        redaction_map = {}
        redacted_text = text
        
        # Apply all PII patterns
        for pii_type, config in {**self.patterns, **self.entity_patterns}.items():
            pattern = config['pattern']
            label = config['label']
            
            matches = list(re.finditer(pattern, redacted_text, re.IGNORECASE))
            
            # Process matches in reverse order to maintain string positions
            for match in reversed(matches):
                original = match.group()
                
                # Generate unique placeholder
                placeholder = f"[{label}_{uuid.uuid4().hex[:8]}]"
                redaction_map[placeholder] = original
                
                # Replace in text
                start, end = match.span()
                redacted_text = redacted_text[:start] + placeholder + redacted_text[end:]
        
        # Detect and redact potential names
        redacted_text, name_map = self._redact_names(redacted_text)
        redaction_map.update(name_map)
        
        return redacted_text, redaction_map
    
    def _redact_names(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Attempt to redact person names
        
        This is a simplified approach. In production, consider using
        NLP libraries like spaCy for better name entity recognition.
        """
        redaction_map = {}
        redacted_text = text
        
        # Pattern for names after indicators (Mr., Ms., etc.)
        for indicator in self.name_indicators:
            pattern = rf'{re.escape(indicator)}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            matches = list(re.finditer(pattern, redacted_text))
            
            for match in reversed(matches):
                name = match.group(1)
                full_match = match.group(0)
                
                placeholder = f"[NAME_{uuid.uuid4().hex[:8]}]"
                redaction_map[placeholder] = name
                
                # Replace only the name part, keep the title
                start = match.start(1)
                end = match.end(1)
                redacted_text = redacted_text[:start] + placeholder + redacted_text[end:]
        
        # Pattern for full names (First Last) in common contexts
        contexts = [
            r'(?:From|To|CC|With|Contact):\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'(?:Hi|Hello|Dear)\s+([A-Z][a-z]+)',
            r'(?:Thanks|Regards|Sincerely),?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        
        for context_pattern in contexts:
            matches = list(re.finditer(context_pattern, redacted_text))
            
            for match in reversed(matches):
                name = match.group(1)
                
                # Skip if already redacted
                if '[' in name and ']' in name:
                    continue
                
                placeholder = f"[NAME_{uuid.uuid4().hex[:8]}]"
                redaction_map[placeholder] = name
                
                start = match.start(1)
                end = match.end(1)
                redacted_text = redacted_text[:start] + placeholder + redacted_text[end:]
        
        return redacted_text, redaction_map
    
    def _redact_sender(self, sender_data: Any) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Redact sender information"""
        redaction_map = {}
        
        if not isinstance(sender_data, dict):
            return sender_data, redaction_map
        
        redacted_sender = sender_data.copy()
        
        if 'emailAddress' in sender_data:
            email_info = sender_data['emailAddress']
            if isinstance(email_info, dict):
                redacted_email_info = email_info.copy()
                
                # Redact email address
                if 'address' in email_info:
                    placeholder = f"[EMAIL_{uuid.uuid4().hex[:8]}]"
                    redaction_map[placeholder] = email_info['address']
                    redacted_email_info['address'] = placeholder
                
                # Redact name
                if 'name' in email_info:
                    placeholder = f"[NAME_{uuid.uuid4().hex[:8]}]"
                    redaction_map[placeholder] = email_info['name']
                    redacted_email_info['name'] = placeholder
                
                redacted_sender['emailAddress'] = redacted_email_info
        
        return redacted_sender, redaction_map
    
    def reconstruct_email(self, redacted_email: Dict[str, Any], 
                         redaction_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Reconstruct original email from redacted version
        
        Args:
            redacted_email: Redacted email data
            redaction_map: Mapping of placeholders to original values
            
        Returns:
            Reconstructed email
        """
        reconstructed = redacted_email.copy()
        
        # Reconstruct text fields
        text_fields = ['subject', 'bodyPreview', 'body']
        
        for field in text_fields:
            if field in reconstructed:
                if field == 'body' and isinstance(reconstructed[field], dict):
                    if 'content' in reconstructed[field]:
                        reconstructed[field]['content'] = self._reconstruct_text(
                            reconstructed[field]['content'], 
                            redaction_map
                        )
                elif isinstance(reconstructed[field], str):
                    reconstructed[field] = self._reconstruct_text(
                        reconstructed[field], 
                        redaction_map
                    )
        
        # Reconstruct sender
        if 'from' in reconstructed and isinstance(reconstructed['from'], dict):
            if 'emailAddress' in reconstructed['from']:
                email_info = reconstructed['from']['emailAddress']
                if isinstance(email_info, dict):
                    for field in ['address', 'name']:
                        if field in email_info and email_info[field] in redaction_map:
                            email_info[field] = redaction_map[email_info[field]]
        
        return reconstructed
    
    def _reconstruct_text(self, text: str, redaction_map: Dict[str, str]) -> str:
        """Reconstruct text by replacing placeholders with original values"""
        reconstructed = text
        
        # Sort by placeholder length (descending) to avoid partial replacements
        sorted_placeholders = sorted(redaction_map.keys(), key=len, reverse=True)
        
        for placeholder in sorted_placeholders:
            if placeholder in reconstructed:
                reconstructed = reconstructed.replace(placeholder, redaction_map[placeholder])
        
        return reconstructed
    
    def get_redaction_summary(self, redaction_map: Dict[str, str]) -> Dict[str, int]:
        """
        Get summary of what was redacted
        
        Args:
            redaction_map: Redaction mapping
            
        Returns:
            Count by PII type
        """
        summary = {}
        
        for placeholder in redaction_map.keys():
            # Extract type from placeholder format [TYPE_hash]
            if '[' in placeholder and '_' in placeholder:
                pii_type = placeholder.split('[')[1].split('_')[0]
                summary[pii_type] = summary.get(pii_type, 0) + 1
        
        return summary
    
    def redact_bulk(self, items: List[Dict[str, Any]], 
                   item_type: str = 'email') -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Redact PII from multiple items
        
        Args:
            items: List of items to redact
            item_type: Type of items ('email' or 'event')
            
        Returns:
            Tuple of (redacted_items, combined_redaction_map)
        """
        redacted_items = []
        combined_map = {}
        
        for item in items:
            if item_type == 'email':
                redacted_item, item_map = self.redact_email(item)
            else:
                # For calendar events, just redact text fields
                redacted_item = item.copy()
                item_map = {}
                
                for field in ['subject', 'body', 'location']:
                    if field in item and item[field]:
                        if isinstance(item[field], dict) and 'displayName' in item[field]:
                            redacted_text, field_map = self._redact_text(item[field]['displayName'])
                            redacted_item[field] = {'displayName': redacted_text}
                            item_map.update(field_map)
                        elif isinstance(item[field], str):
                            redacted_text, field_map = self._redact_text(item[field])
                            redacted_item[field] = redacted_text
                            item_map.update(field_map)
            
            redacted_items.append(redacted_item)
            combined_map.update(item_map)
        
        return redacted_items, combined_map
    
    def create_privacy_report(self, redaction_maps: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Create a privacy report for redacted content
        
        Args:
            redaction_maps: List of redaction mappings
            
        Returns:
            Privacy report with statistics
        """
        total_redactions = sum(len(m) for m in redaction_maps)
        
        # Combine all maps
        combined_summary = {}
        for rmap in redaction_maps:
            summary = self.get_redaction_summary(rmap)
            for pii_type, count in summary.items():
                combined_summary[pii_type] = combined_summary.get(pii_type, 0) + count
        
        return {
            'total_items_processed': len(redaction_maps),
            'total_redactions': total_redactions,
            'redactions_by_type': combined_summary,
            'privacy_level': self._calculate_privacy_level(total_redactions)
        }
    
    def _calculate_privacy_level(self, redaction_count: int) -> str:
        """Calculate privacy level based on redaction count"""
        if redaction_count == 0:
            return 'none'
        elif redaction_count < 10:
            return 'low'
        elif redaction_count < 50:
            return 'medium'
        else:
            return 'high'
