"""
Main application forms

This module contains Flask-WTF forms for the main application.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, ValidationError
import pytz


class SettingsForm(FlaskForm):
    """User settings form"""
    
    # Digest timing
    digest_time = StringField('Daily Digest Time', validators=[
        DataRequired(message='Please specify a time for your daily digest')
    ], default='09:00')
    
    # Timezone selection
    timezone = SelectField('Timezone', validators=[
        DataRequired(message='Please select your timezone')
    ])
    
    # Privacy settings
    privacy_mode = BooleanField('Enable Privacy Mode (Redact PII)')
    
    # Working hours
    working_hours_start = IntegerField('Work Day Starts', validators=[
        DataRequired(message='Please specify when your work day starts'),
        NumberRange(min=0, max=23, message='Hour must be between 0 and 23')
    ], default=9)
    
    working_hours_end = IntegerField('Work Day Ends', validators=[
        DataRequired(message='Please specify when your work day ends'),
        NumberRange(min=0, max=23, message='Hour must be between 0 and 23')
    ], default=17)
    
    # Notification preferences
    email_notifications = BooleanField('Send Email Notifications')
    
    # Digest format
    digest_format = SelectField('Digest Format', choices=[
        ('html', 'HTML (Rich formatting)'),
        ('text', 'Plain Text')
    ], default='html')
    
    submit = SubmitField('Save Settings')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate timezone choices
        self.timezone.choices = self._get_timezone_choices()
    
    def _get_timezone_choices(self):
        """Get list of timezone choices"""
        common_timezones = [
            'UTC',
            'US/Eastern',
            'US/Central',
            'US/Mountain',
            'US/Pacific',
            'Europe/London',
            'Europe/Paris',
            'Europe/Berlin',
            'Asia/Tokyo',
            'Asia/Shanghai',
            'Asia/Singapore',
            'Australia/Sydney',
            'Pacific/Auckland'
        ]
        
        choices = [(tz, tz) for tz in common_timezones]
        choices.extend([
            ('---', '--- All Timezones ---'),
            *[(tz, tz) for tz in sorted(pytz.all_timezones) if tz not in common_timezones]
        ])
        
        return choices
    
    def validate_working_hours_end(self, field):
        """Validate that work end time is after start time"""
        if field.data <= self.working_hours_start.data:
            raise ValidationError('Work end time must be after start time')
    
    def validate_digest_time(self, field):
        """Validate digest time format"""
        try:
            # Check if time is in HH:MM format
            parts = field.data.split(':')
            if len(parts) != 2:
                raise ValueError
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            if not (0 <= hour <= 23):
                raise ValidationError('Hour must be between 0 and 23')
            
            if not (0 <= minute <= 59):
                raise ValidationError('Minute must be between 0 and 59')
                
        except ValueError:
            raise ValidationError('Time must be in HH:MM format (e.g., 09:00)')


class FeedbackForm(FlaskForm):
    """User feedback form"""
    subject = StringField('Subject', validators=[
        DataRequired(message='Please provide a subject')
    ])
    
    feedback_type = SelectField('Type', choices=[
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('improvement', 'Improvement Suggestion'),
        ('other', 'Other')
    ], default='improvement')
    
    message = StringField('Message', validators=[
        DataRequired(message='Please provide your feedback')
    ])
    
    submit = SubmitField('Submit Feedback')
