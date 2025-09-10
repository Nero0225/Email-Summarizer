"""
Microsoft Service

This module handles Microsoft Graph API integration for
accessing Office 365 emails and calendar data.
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
from msal import ConfidentialClientApplication
from flask import current_app, url_for


class MicrosoftService:
    """Service class for Microsoft Graph API operations"""
    
    def __init__(self):
        self.client_id = current_app.config.get('AZURE_CLIENT_ID')
        self.client_secret = current_app.config.get('AZURE_CLIENT_SECRET')
        self.tenant_id = current_app.config.get('AZURE_TENANT_ID', 'common')
        self.redirect_uri = current_app.config.get('REDIRECT_URI')
        
        # Graph API configuration
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        
        # Required scopes
        self.scopes = [
            "https://graph.microsoft.com/Mail.Read",
            "https://graph.microsoft.com/Calendars.Read",
            "https://graph.microsoft.com/User.Read"
        ]
        
        # Initialize MSAL app
        self._init_msal_app()
    
    def _init_msal_app(self):
        """Initialize MSAL application"""
        if self.client_id and self.client_secret:
            try:
                self.msal_app = ConfidentialClientApplication(
                    client_id=self.client_id,
                    client_credential=self.client_secret,
                    authority=self.authority
                )
            except Exception as e:
                current_app.logger.error(f"MSAL initialization failed: {e}")
                self.msal_app = None
        else:
            self.msal_app = None
            current_app.logger.warning("Microsoft authentication not configured")
    
    def get_auth_url(self) -> Optional[str]:
        """
        Get Microsoft OAuth2 authorization URL
        
        Returns:
            Authorization URL or None if not configured
        """
        if not self.msal_app:
            return None
        
        # Generate dynamic redirect URI
        if not self.redirect_uri:
            self.redirect_uri = url_for('auth.microsoft_callback', _external=True)
        
        auth_url = self.msal_app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        return auth_url
    
    def get_token_from_code(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from OAuth callback
            
        Returns:
            Token response dictionary or None
        """
        if not self.msal_app:
            return None
        
        try:
            # Generate dynamic redirect URI if not set
            if not self.redirect_uri:
                self.redirect_uri = url_for('auth.microsoft_callback', _external=True)
            
            result = self.msal_app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if 'error' in result:
                current_app.logger.error(f"Token acquisition error: {result.get('error_description', result['error'])}")
                return None
                
            return result
            
        except Exception as e:
            current_app.logger.error(f"Token acquisition failed: {e}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token response or None
        """
        if not self.msal_app:
            return None
        
        try:
            # MSAL doesn't have direct refresh token method in Python
            # We need to use the underlying OAuth2 endpoint
            token_endpoint = f"{self.authority}/oauth2/v2.0/token"
            
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'scope': ' '.join(self.scopes)
            }
            
            response = requests.post(token_endpoint, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Token refresh failed: {response.text}")
                return None
                
        except Exception as e:
            current_app.logger.error(f"Token refresh exception: {e}")
            return None
    
    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Get user profile information
        
        Args:
            access_token: Valid access token
            
        Returns:
            User profile dictionary
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.graph_endpoint}/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Profile API error: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            current_app.logger.error(f"Error fetching user profile: {e}")
            return {}
    
    def get_user_emails(self, access_token: str, days_back: int = 2) -> List[Dict[str, Any]]:
        """
        Fetch user emails according to PRD requirements
        
        Args:
            access_token: Valid access token
            days_back: Number of days to look back
            
        Returns:
            List of email messages
        """
        if not access_token:
            return []
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Calculate date filter based on PRD requirements
        now = datetime.now(pytz.UTC)
        
        # If Monday, include weekend (Sat + Sun)
        if now.weekday() == 0:  # Monday
            start_date = now - timedelta(days=2)  # Saturday
        else:
            start_date = now - timedelta(days=days_back)
        
        # Format for Graph API
        start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Graph API query parameters per PRD
        params = {
            '$filter': f"receivedDateTime ge {start_date_str} and parentFolderId eq 'inbox'",
            '$select': 'id,subject,from,receivedDateTime,bodyPreview,conversationId,isRead,importance,hasAttachments,body',
            '$orderby': 'receivedDateTime desc',
            '$top': current_app.config.get('MAX_EMAILS_PER_DIGEST', 200)
        }
        
        try:
            response = requests.get(
                f"{self.graph_endpoint}/me/messages",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('value', [])
                
                # Handle pagination if needed
                while '@odata.nextLink' in data and len(emails) < params['$top']:
                    response = requests.get(data['@odata.nextLink'], headers=headers, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        emails.extend(data.get('value', []))
                    else:
                        break
                
                return emails[:params['$top']]  # Ensure we don't exceed the limit
            else:
                current_app.logger.error(f"Graph API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            current_app.logger.error(f"Error fetching emails: {e}")
            return []
    
    def get_user_calendar_events(self, access_token: str, date: datetime = None) -> List[Dict[str, Any]]:
        """
        Fetch today's calendar events
        
        Args:
            access_token: Valid access token
            date: Date to fetch events for (default: today)
            
        Returns:
            List of calendar events
        """
        if not access_token:
            return []
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Use provided date or today
        if not date:
            date = datetime.now(pytz.UTC)
        
        # Get start and end of day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        start_str = start_of_day.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_str = end_of_day.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        params = {
            '$filter': f"start/dateTime ge '{start_str}' and end/dateTime le '{end_str}'",
            '$select': 'id,subject,start,end,organizer,attendees,body,location,showAs,isAllDay,isCancelled',
            '$orderby': 'start/dateTime',
            '$top': 50  # Reasonable limit for daily events
        }
        
        try:
            response = requests.get(
                f"{self.graph_endpoint}/me/events",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('value', [])
                
                # Filter out cancelled events
                events = [e for e in events if not e.get('isCancelled', False)]
                
                return events
            else:
                current_app.logger.error(f"Calendar API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            current_app.logger.error(f"Error fetching calendar events: {e}")
            return []
    
    def test_connection(self, access_token: str) -> bool:
        """
        Test if access token is valid
        
        Args:
            access_token: Access token to test
            
        Returns:
            True if token is valid, False otherwise
        """
        if not access_token:
            return False
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.graph_endpoint}/me",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def revoke_consent(self, user_id: str) -> bool:
        """
        Revoke user consent (note: this is typically done through Azure portal)
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        # In a production app, you might want to:
        # 1. Remove stored tokens from database
        # 2. Notify the user to revoke consent in their Microsoft account settings
        # 3. Log the revocation
        
        current_app.logger.info(f"Consent revocation requested for user {user_id}")
        return True
