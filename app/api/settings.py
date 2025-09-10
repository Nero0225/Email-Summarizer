"""
Settings API endpoints

This module provides API endpoints for user settings management.
"""
from flask import jsonify, request, current_app
from flask_login import current_user
from app import db
from app.api import api_bp
from app.models import UserSettings
from app.utils.decorators import api_login_required


@api_bp.route('/settings', methods=['GET'])
@api_login_required
def get_settings():
    """
    Get current user settings
    
    Returns:
        JSON response with user settings
        
    Status codes:
        200: Success
        401: Unauthorized
    """
    settings = current_user.settings
    if not settings:
        # Create default settings if not exists
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    
    return jsonify({
        'status': 'success',
        'settings': settings.to_dict()
    })


@api_bp.route('/settings', methods=['PUT', 'PATCH'])
@api_login_required
def update_settings():
    """
    Update user settings
    
    Request body:
        JSON object with settings to update
        
    Returns:
        JSON response with updated settings
        
    Status codes:
        200: Success
        400: Bad request (validation error)
        401: Unauthorized
    """
    data = request.get_json()
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400
    
    # Get or create settings
    settings = current_user.settings
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
    
    # Validate settings
    errors = validate_settings(data)
    if errors:
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': errors
        }), 400
    
    try:
        # Update settings
        settings.update_settings(data)
        
        return jsonify({
            'status': 'success',
            'settings': settings.to_dict(),
            'message': 'Settings updated successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f'Settings update error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to update settings'
        }), 500


@api_bp.route('/settings/<key>', methods=['GET'])
@api_login_required
def get_setting(key):
    """
    Get a specific setting value
    
    Args:
        key: Setting key to retrieve
        
    Returns:
        JSON response with setting value
        
    Status codes:
        200: Success
        401: Unauthorized
        404: Setting not found
    """
    settings = current_user.settings
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    
    value = settings.get_setting(key)
    if value is None and key not in UserSettings.DEFAULT_SETTINGS:
        return jsonify({
            'status': 'error',
            'message': f'Setting "{key}" not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'key': key,
        'value': value
    })


@api_bp.route('/settings/<key>', methods=['PUT'])
@api_login_required
def update_setting(key):
    """
    Update a specific setting
    
    Args:
        key: Setting key to update
        
    Request body:
        JSON object with 'value' field
        
    Returns:
        JSON response with updated setting
        
    Status codes:
        200: Success
        400: Bad request
        401: Unauthorized
    """
    data = request.get_json()
    if not data or 'value' not in data:
        return jsonify({
            'status': 'error',
            'message': 'No value provided'
        }), 400
    
    # Validate specific setting
    errors = validate_setting(key, data['value'])
    if errors:
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': errors
        }), 400
    
    # Get or create settings
    settings = current_user.settings
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
    
    try:
        settings.update_setting(key, data['value'])
        
        return jsonify({
            'status': 'success',
            'key': key,
            'value': data['value'],
            'message': f'Setting "{key}" updated successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f'Setting update error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to update setting'
        }), 500


@api_bp.route('/settings/reset', methods=['POST'])
@api_login_required
def reset_settings():
    """
    Reset all settings to defaults
    
    Returns:
        JSON response with default settings
        
    Status codes:
        200: Success
        401: Unauthorized
    """
    settings = current_user.settings
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
    
    try:
        # Reset to defaults
        settings.settings_data = UserSettings.DEFAULT_SETTINGS.copy()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'settings': settings.to_dict(),
            'message': 'Settings reset to defaults'
        })
        
    except Exception as e:
        current_app.logger.error(f'Settings reset error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to reset settings'
        }), 500


def validate_settings(settings_data):
    """
    Validate settings data
    
    Args:
        settings_data: Dictionary of settings to validate
        
    Returns:
        Dictionary of validation errors (empty if valid)
    """
    errors = {}
    
    for key, value in settings_data.items():
        key_errors = validate_setting(key, value)
        if key_errors:
            errors[key] = key_errors
    
    return errors


def validate_setting(key, value):
    """
    Validate a specific setting
    
    Args:
        key: Setting key
        value: Setting value
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if key == 'digest_time':
        # Validate time format HH:MM
        try:
            parts = value.split(':')
            if len(parts) != 2:
                errors.append('Time must be in HH:MM format')
            else:
                hour = int(parts[0])
                minute = int(parts[1])
                if not (0 <= hour <= 23):
                    errors.append('Hour must be between 0 and 23')
                if not (0 <= minute <= 59):
                    errors.append('Minute must be between 0 and 59')
        except (ValueError, AttributeError):
            errors.append('Invalid time format')
    
    elif key == 'timezone':
        # Validate timezone
        import pytz
        if value not in pytz.all_timezones:
            errors.append('Invalid timezone')
    
    elif key in ['working_hours_start', 'working_hours_end']:
        # Validate working hours
        try:
            hour = int(value)
            if not (0 <= hour <= 23):
                errors.append('Hour must be between 0 and 23')
        except (ValueError, TypeError):
            errors.append('Must be a valid hour (0-23)')
    
    elif key in ['privacy_mode', 'email_notifications', 'use_test_data']:
        # Validate boolean settings
        if not isinstance(value, bool):
            errors.append('Must be true or false')
    
    elif key == 'digest_format':
        # Validate digest format
        if value not in ['html', 'text']:
            errors.append('Must be "html" or "text"')
    
    return errors
