"""
Authentication forms

This module contains Flask-WTF forms for authentication.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from app.models import User


class LoginForm(FlaskForm):
    """Login form for user authentication"""
    username = StringField('Username or Email', validators=[
        DataRequired(message='Please enter your username or email')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    """Registration form for new users"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters'),
        Regexp('^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(min=2, max=128, message='Full name must be between 2 and 128 characters')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=128)
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Validate that username is not already taken"""
        user = User.query.filter_by(username=username.data.lower()).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different username.')
    
    def validate_email(self, email):
        """Validate that email is not already registered"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or log in.')


class ChangePasswordForm(FlaskForm):
    """Form for changing user password"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Please enter your current password')
    ])
    
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='Please enter a new password'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])
    
    submit = SubmitField('Change Password')


class ResetPasswordRequestForm(FlaskForm):
    """Form for requesting password reset"""
    email = StringField('Email', validators=[
        DataRequired(message='Please enter your email'),
        Email(message='Please enter a valid email address')
    ])
    
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    """Form for resetting password with token"""
    password = PasswordField('New Password', validators=[
        DataRequired(message='Please enter a new password'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    submit = SubmitField('Reset Password')
