"""
Error handlers for Email Summarizer application

This module provides centralized error handling for the application.
"""
from flask import render_template, jsonify, request
from werkzeug.exceptions import HTTPException


def handle_404(e):
    """Handle 404 Not Found errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    return render_template('errors/404.html'), 404


def handle_403(e):
    """Handle 403 Forbidden errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    return render_template('errors/403.html'), 403


def handle_500(e):
    """Handle 500 Internal Server errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    return render_template('errors/500.html'), 500


def handle_api_error(e):
    """Handle API errors uniformly"""
    # If it's an HTTP exception, use its code and description
    if isinstance(e, HTTPException):
        return jsonify({
            'status': 'error',
            'error': e.name,
            'message': e.description
        }), e.code
    
    # For other exceptions, return 500
    from flask import current_app
    current_app.logger.error(f'Unhandled exception: {str(e)}')
    
    # Don't expose internal error details in production
    if current_app.debug:
        return jsonify({
            'status': 'error',
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
    
    return jsonify({
        'status': 'error',
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


class AppError(Exception):
    """Base application error class"""
    status_code = 500
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv


class ValidationError(AppError):
    """Validation error"""
    status_code = 400


class AuthenticationError(AppError):
    """Authentication error"""
    status_code = 401


class AuthorizationError(AppError):
    """Authorization error"""
    status_code = 403


class ResourceNotFoundError(AppError):
    """Resource not found error"""
    status_code = 404


class ConflictError(AppError):
    """Resource conflict error"""
    status_code = 409


class RateLimitError(AppError):
    """Rate limit exceeded error"""
    status_code = 429


class ExternalServiceError(AppError):
    """External service error (e.g., Microsoft API)"""
    status_code = 503
    
    def __init__(self, service_name, message, status_code=None):
        super().__init__(message, status_code)
        self.service_name = service_name
    
    def to_dict(self):
        rv = super().to_dict()
        rv['service'] = self.service_name
        return rv


def register_error_handlers(app):
    """
    Register all error handlers with the Flask app
    
    This function is called from the application factory
    """
    @app.errorhandler(AppError)
    def handle_app_error(error):
        """Handle custom application errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(AuthenticationError)
    def handle_auth_error(error):
        """Handle authentication errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(AuthorizationError)
    def handle_authz_error(error):
        """Handle authorization errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(ResourceNotFoundError)
    def handle_not_found_error(error):
        """Handle resource not found errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(error):
        """Handle rate limit errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(ExternalServiceError)
    def handle_external_error(error):
        """Handle external service errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
