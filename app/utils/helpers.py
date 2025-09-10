"""
Helper functions for Email Summarizer application

This module provides utility functions used throughout the application.
"""
import os
import re
import string
import secrets
from datetime import datetime
from typing import Optional, Any
from flask import current_app
from flask_login import current_user


def get_current_user_id() -> Optional[int]:
    """
    Get current user ID safely
    
    Returns:
        User ID if authenticated, None otherwise
    """
    if current_user and current_user.is_authenticated:
        return current_user.id
    return None


def format_datetime(dt: datetime, format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format datetime object to string
    
    Args:
        dt: Datetime object
        format_string: Format string (default: YYYY-MM-DD HH:MM:SS)
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return ''
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    
    return dt.strftime(format_string)


def format_relative_time(dt: datetime) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago")
    
    Args:
        dt: Datetime object
        
    Returns:
        Relative time string
    """
    if not dt:
        return 'Never'
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return str(dt)
    
    now = datetime.utcnow()
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


def generate_random_string(length: int = 32, 
                         include_digits: bool = True,
                         include_punctuation: bool = False) -> str:
    """
    Generate a cryptographically secure random string
    
    Args:
        length: Length of the string
        include_digits: Include digits in the string
        include_punctuation: Include punctuation in the string
        
    Returns:
        Random string
    """
    alphabet = string.ascii_letters
    
    if include_digits:
        alphabet += string.digits
    
    if include_punctuation:
        alphabet += string.punctuation
    
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated text
    """
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_domain(email: str) -> str:
    """
    Extract domain from email address
    
    Args:
        email: Email address
        
    Returns:
        Domain name
    """
    if not email or '@' not in email:
        return ''
    
    return email.split('@')[1].lower()


def is_valid_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Filename
        
    Returns:
        File extension (lowercase, without dot)
    """
    if not filename or '.' not in filename:
        return ''
    
    return filename.rsplit('.', 1)[1].lower()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def parse_boolean(value: Any) -> bool:
    """
    Parse various boolean representations
    
    Args:
        value: Value to parse
        
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value = value.lower().strip()
        return value in ('true', 'yes', '1', 'on', 'enabled')
    
    return bool(value)


def get_client_ip(request) -> str:
    """
    Get client IP address from request
    
    Args:
        request: Flask request object
        
    Returns:
        Client IP address
    """
    # Check for forwarded IP (if behind proxy)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP if multiple are present
        return forwarded_for.split(',')[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fall back to remote address
    return request.remote_addr or 'unknown'


def mask_email(email: str) -> str:
    """
    Mask email address for privacy
    
    Args:
        email: Email address
        
    Returns:
        Masked email (e.g., j***@example.com)
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 3:
        masked_local = local[0] + '*' * (len(local) - 1)
    else:
        masked_local = local[0] + '*' * 3 + local[-1]
    
    return f"{masked_local}@{domain}"


def deep_update(base_dict: dict, update_dict: dict) -> dict:
    """
    Deep update a dictionary
    
    Args:
        base_dict: Base dictionary
        update_dict: Dictionary with updates
        
    Returns:
        Updated dictionary
    """
    for key, value in update_dict.items():
        if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
            base_dict[key] = deep_update(base_dict[key], value)
        else:
            base_dict[key] = value
    
    return base_dict


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
