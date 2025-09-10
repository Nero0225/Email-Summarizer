"""
Custom decorators for Email Summarizer application

This module provides decorators for authentication, authorization,
rate limiting, and other cross-cutting concerns.
"""
from functools import wraps
from datetime import date
from flask import jsonify, request, current_app, g
from flask_login import current_user, login_required
from app.models import User, UserRole, DailyUsage


def admin_required(f):
    """
    Decorator to require admin role
    Must be used after @login_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def api_login_required(f):
    """
    Decorator for API endpoints requiring authentication
    Returns JSON error responses instead of redirects
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required',
                'error_type': 'unauthorized'
            }), 401
        
        if not current_user.is_active:
            return jsonify({
                'status': 'error',
                'message': 'Account is not active',
                'error_type': 'forbidden'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def check_daily_limit(f):
    """
    Decorator to check daily digest generation limit
    Must be used after authentication decorators
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check daily limit
        today = date.today()
        daily_usage = DailyUsage.query.filter_by(
            user_id=current_user.id,
            usage_date=today
        ).first()
        
        daily_limit = current_app.config.get('DAILY_DIGEST_LIMIT', 1)
        
        if daily_usage and daily_usage.digest_count >= daily_limit:
            return jsonify({
                'status': 'error',
                'error_type': 'daily_limit',
                'message': "You've already generated today's digest. Please try again tomorrow.",
                'next_available': 'Tomorrow at midnight'
            }), 429
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(calls=10, window=60):
    """
    Simple rate limiting decorator
    
    Args:
        calls: Number of allowed calls
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip if rate limiting is disabled
            if not current_app.config.get('RATELIMIT_ENABLED', True):
                return f(*args, **kwargs)
            
            # Get client identifier
            if current_user.is_authenticated:
                client_id = f"user:{current_user.id}"
            else:
                client_id = f"ip:{request.remote_addr}"
            
            # This is a simplified implementation
            # In production, use Redis or similar for distributed rate limiting
            cache_key = f"rate_limit:{f.__name__}:{client_id}"
            
            # For now, just proceed
            # TODO: Implement actual rate limiting with Redis
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def require_api_key(f):
    """
    Decorator to require API key for certain endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'API key required'
            }), 401
        
        # Validate API key (simplified - in production, check against database)
        valid_api_key = current_app.config.get('API_KEY')
        if api_key != valid_api_key:
            return jsonify({
                'status': 'error',
                'message': 'Invalid API key'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_json(*required_fields):
    """
    Decorator to validate required JSON fields in request
    
    Args:
        *required_fields: Field names that must be present
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Content-Type must be application/json'
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No JSON data provided'
                }), 400
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            # Store validated data in g for use in view
            g.json_data = data
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def async_task(f):
    """
    Decorator to run function asynchronously
    Note: This is a placeholder. In production, use Celery or similar
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, just run synchronously
        # TODO: Implement with Celery for production
        return f(*args, **kwargs)
    
    return decorated_function


def cache_result(timeout=300):
    """
    Simple caching decorator
    
    Args:
        timeout: Cache timeout in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This is a simplified implementation
            # In production, use Redis or similar for caching
            
            # For now, just execute the function
            # TODO: Implement actual caching
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def measure_performance(f):
    """
    Decorator to measure function execution time
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Log performance
        current_app.logger.info(
            f'{f.__name__} executed in {execution_time:.2f} seconds'
        )
        
        # Add execution time to response if it's a dict
        if isinstance(result, dict):
            result['_execution_time'] = execution_time
        
        return result
    
    return decorated_function
