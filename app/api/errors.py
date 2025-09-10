"""
API error handlers

This module provides error handling for API endpoints.
"""
from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from app.api import api_bp


def error_response(status_code, message=None):
    """
    Create a JSON error response
    
    Args:
        status_code: HTTP status code
        message: Error message (optional)
        
    Returns:
        Flask response object with JSON error
    """
    payload = {
        'status': 'error',
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')
    }
    if message:
        payload['message'] = message
    
    response = jsonify(payload)
    response.status_code = status_code
    return response


def bad_request(message='Bad request'):
    """400 Bad Request error response"""
    return error_response(400, message)


def unauthorized(message='Unauthorized'):
    """401 Unauthorized error response"""
    return error_response(401, message)


def forbidden(message='Forbidden'):
    """403 Forbidden error response"""
    return error_response(403, message)


def not_found(message='Not found'):
    """404 Not Found error response"""
    return error_response(404, message)


def method_not_allowed(message='Method not allowed'):
    """405 Method Not Allowed error response"""
    return error_response(405, message)


def unprocessable_entity(message='Unprocessable entity'):
    """422 Unprocessable Entity error response"""
    return error_response(422, message)


def too_many_requests(message='Too many requests'):
    """429 Too Many Requests error response"""
    return error_response(429, message)


def internal_error(message='Internal server error'):
    """500 Internal Server Error response"""
    return error_response(500, message)


# API-specific error handlers
@api_bp.errorhandler(400)
def handle_bad_request(e):
    """Handle 400 errors in API"""
    return bad_request(str(e))


@api_bp.errorhandler(401)
def handle_unauthorized(e):
    """Handle 401 errors in API"""
    return unauthorized('Authentication required')


@api_bp.errorhandler(403)
def handle_forbidden(e):
    """Handle 403 errors in API"""
    return forbidden('Access denied')


@api_bp.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors in API"""
    return not_found('Resource not found')


@api_bp.errorhandler(405)
def handle_method_not_allowed(e):
    """Handle 405 errors in API"""
    return method_not_allowed(f'The {e.method} method is not allowed for this endpoint')


@api_bp.errorhandler(422)
def handle_unprocessable_entity(e):
    """Handle 422 errors in API"""
    return unprocessable_entity(str(e))


@api_bp.errorhandler(429)
def handle_too_many_requests(e):
    """Handle 429 errors in API"""
    return too_many_requests('Rate limit exceeded')


@api_bp.errorhandler(500)
def handle_internal_error(e):
    """Handle 500 errors in API"""
    # Log the error
    from flask import current_app
    current_app.logger.error(f'Internal error: {str(e)}')
    
    # Don't expose internal error details in production
    if current_app.debug:
        return internal_error(str(e))
    return internal_error()


# Custom exception classes
class APIError(Exception):
    """Base API exception class"""
    status_code = 500
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert exception to dictionary for JSON response"""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv


class ValidationError(APIError):
    """Validation error exception"""
    status_code = 400
    
    def __init__(self, message, field=None, errors=None):
        super().__init__(message)
        self.field = field
        self.errors = errors
    
    def to_dict(self):
        """Include validation errors in response"""
        rv = super().to_dict()
        if self.field:
            rv['field'] = self.field
        if self.errors:
            rv['errors'] = self.errors
        return rv


class AuthenticationError(APIError):
    """Authentication error exception"""
    status_code = 401


class AuthorizationError(APIError):
    """Authorization error exception"""
    status_code = 403


class ResourceNotFoundError(APIError):
    """Resource not found exception"""
    status_code = 404


class RateLimitError(APIError):
    """Rate limit exceeded exception"""
    status_code = 429


# Register custom exception handlers
@api_bp.errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
