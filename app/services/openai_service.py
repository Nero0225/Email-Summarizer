"""
OpenAI Service for Email and Calendar Summarization

This module provides OpenAI-powered summarization capabilities
for emails and calendar events.
"""
from openai import OpenAI
import re
import json
from typing import Dict, List, Any, Optional
from flask import current_app


class OpenAIService:
    """Service for OpenAI-powered text summarization and analysis"""
    
    def __init__(self):
        """Initialize OpenAI service with API key from config"""
        self.api_key = current_app.config.get('OPENAI_API_KEY')
        self.model = current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            current_app.logger.warning("OpenAI API key not configured")
    
    def summarize_emails(self, conversations: Dict[str, Any], 
                        include_private: bool = False) -> Dict[str, Any]:
        """
        Summarize email conversations using OpenAI
        
        Args:
            conversations: Processed email conversations
            include_private: Whether to include private content
            
        Returns:
            AI-generated summaries for each conversation
        """
        if not self.client:
            return self._fallback_summary(conversations)
        
        summaries = {}
        
        for conv_id, conversation in conversations.items():
            try:
                # Prepare email content for summarization
                emails = conversation.get('emails', [])
                
                # Build context for OpenAI
                context = self._build_email_context(emails, include_private)
                
                # Generate summary using OpenAI
                summary = self._generate_email_summary(
                    context, 
                    conversation.get('classification', {})
                )
                
                summaries[conv_id] = summary
                
            except Exception as e:
                current_app.logger.error(f"OpenAI summarization error: {str(e)}")
                summaries[conv_id] = self._fallback_conversation_summary(conversation)
        
        return summaries
    
    def summarize_calendar(self, calendar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-powered calendar insights for today
        
        Args:
            calendar_data: Processed calendar data
            
        Returns:
            AI-generated calendar summary with insights
        """
        if not self.client:
            return calendar_data
        
        try:
            meetings = calendar_data.get('meetings', [])
            
            # Build prompt for calendar analysis
            prompt = self._build_calendar_prompt(meetings, calendar_data)
            
            # Get AI insights
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an executive assistant providing concise, actionable calendar insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            ai_insights = response.choices[0].message.content
            
            # Add AI insights to calendar data
            calendar_data['ai_insights'] = ai_insights
            calendar_data['ai_summary'] = self._extract_key_insights(ai_insights)
            
        except Exception as e:
            current_app.logger.error(f"OpenAI calendar analysis error: {str(e)}")
        
        return calendar_data
    
    def classify_with_ai(self, email_content: str) -> Dict[str, Any]:
        """
        Use OpenAI to classify emails using 4D framework
        
        Args:
            email_content: Email text to classify
            
        Returns:
            Classification with AI reasoning
        """
        if not self.client:
            return {"action": "DO", "reasoning": "Default classification"}
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Classify this email using the 4D framework:
                        - DO: Requires immediate action or response
                        - DELEGATE: Should be assigned to someone else
                        - DEFER: Can be handled later
                        - DELETE: No action needed, can be archived
                        
                        Respond with JSON: {"action": "ACTION", "reasoning": "brief explanation"}"""
                    },
                    {
                        "role": "user",
                        "content": email_content[:1000]  # Limit context length
                    }
                ],
                max_tokens=100,
                temperature=0.5
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            current_app.logger.error(f"AI classification error: {str(e)}")
            return {"action": "DO", "reasoning": "Classification failed, defaulting to DO"}
    
    def _build_email_context(self, emails: List[Dict[str, Any]], 
                            include_private: bool) -> str:
        """Build context string from emails for OpenAI"""
        context_parts = []
        
        for email in emails[:5]:  # Limit to recent 5 emails
            sender = email.get('from', {}).get('emailAddress', {}).get('name', 'Unknown')
            subject = email.get('subject', 'No Subject')
            body = email.get('bodyPreview', '')
            
            if not include_private:
                # Redact private information
                body = self._redact_private_info(body)
            
            context_parts.append(f"From: {sender}\nSubject: {subject}\n{body[:200]}...")
        
        return "\n\n".join(context_parts)
    
    def _generate_email_summary(self, context: str, 
                               classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email summary using OpenAI"""
        action = classification.get('action', 'DO')
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"""Summarize this email conversation concisely.
                    The email is classified as '{action}' action.
                    Focus on: 1) Main topic 2) Key action items 3) Urgency level"""
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        summary_text = response.choices[0].message.content
        
        # Extract structured information
        return {
            'summary': summary_text,
            'key_points': self._extract_key_points(summary_text),
            'urgency': self._detect_urgency(summary_text),
            'action_items': self._extract_action_items(summary_text)
        }
    
    def _build_calendar_prompt(self, meetings: List[Dict[str, Any]], 
                              calendar_data: Dict[str, Any]) -> str:
        """Build prompt for calendar analysis"""
        total_hours = calendar_data.get('total_meeting_hours', 0)
        focus_hours = calendar_data.get('focus_time_hours', 0)
        
        prompt = f"""Analyze today's calendar:
        - {len(meetings)} meetings totaling {total_hours} hours
        - {focus_hours} hours of focus time available
        
        Meetings:
        """
        
        for meeting in meetings[:10]:  # Limit to 10 meetings
            prompt += f"\n- {meeting['start_time']}-{meeting['end_time']}: {meeting['subject']}"
            if meeting.get('attendees_count', 0) > 2:
                prompt += f" ({meeting['attendees_count']} attendees)"
        
        prompt += "\n\nProvide: 1) Day overview 2) Time management tips 3) Meeting preparation priorities"
        
        return prompt
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from AI-generated text"""
        # Simple extraction - can be improved with more sophisticated parsing
        lines = text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line and any(marker in line for marker in ['•', '-', '1)', '2)', '3)']):
                key_points.append(line.strip('•-123) '))
        
        return key_points[:5]  # Return top 5 points
    
    def _detect_urgency(self, text: str) -> str:
        """Detect urgency level from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['urgent', 'asap', 'immediately', 'critical']):
            return 'high'
        elif any(word in text_lower for word in ['soon', 'priority', 'important']):
            return 'medium'
        else:
            return 'low'
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from summary"""
        action_items = []
        
        # Look for action-oriented phrases
        action_indicators = ['need to', 'should', 'must', 'requires', 'please', 'action:']
        
        sentences = text.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in action_indicators):
                action_items.append(sentence.strip())
        
        return action_items[:3]  # Return top 3 action items
    
    def _redact_private_info(self, text: str) -> str:
        """Simple redaction of private information"""
        # Email pattern
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        # Phone pattern
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        # SSN pattern
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        return text
    
    def _extract_key_insights(self, insights_text: str) -> str:
        """Extract key insights from AI response"""
        # Take first paragraph or first 2 sentences
        paragraphs = insights_text.split('\n\n')
        if paragraphs:
            return paragraphs[0]
        
        sentences = insights_text.split('.')
        if len(sentences) >= 2:
            return '. '.join(sentences[:2]) + '.'
        
        return insights_text[:200]
    
    def _fallback_summary(self, conversations: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback summaries when OpenAI is not available"""
        summaries = {}
        for conv_id, conv in conversations.items():
            summaries[conv_id] = {
                'summary': conv.get('summary', 'Email conversation'),
                'key_points': [],
                'urgency': 'medium',
                'action_items': []
            }
        return summaries
    
    def _fallback_conversation_summary(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback summary for individual conversation"""
        return {
            'summary': conversation.get('summary', 'Email conversation'),
            'key_points': [],
            'urgency': 'medium',
            'action_items': []
        }
