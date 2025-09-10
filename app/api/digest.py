"""
Digest API endpoints

This module provides API endpoints for digest generation and retrieval.
"""
from datetime import date
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.api import api_bp
from app.models import DigestRecord, DailyUsage
from app.services.digest_service import DigestService
from app.utils.decorators import api_login_required, check_daily_limit


@api_bp.route('/digest/generate', methods=['POST'])
@api_login_required
@check_daily_limit
def generate_digest():
    """
    Generate a new daily digest
    
    Returns:
        JSON response with digest data or error message
        
    Status codes:
        200: Success
        400: Bad request (validation error)
        401: Unauthorized
        429: Daily limit exceeded
        500: Internal server error
    """
    try:
        # Get request options
        data = request.get_json() or {}
        options = {
            'force_refresh': data.get('force_refresh', False),
            'include_raw_data': data.get('include_raw_data', False)
        }
        
        # Generate digest
        digest_service = DigestService()
        result = digest_service.generate_digest_for_user(
            current_user.id,
            **options
        )
        
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'digest_id': result['digest_id'],
                'digest': result.get('digest_data'),
                'generation_info': {
                    'generated_at': result.get('generated_at'),
                    'processing_time': result.get('processing_time'),
                    'email_count': result.get('email_count'),
                    'meeting_count': result.get('meeting_count')
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'error_type': result.get('error_type', 'generation_failed'),
                'message': result.get('message', 'Failed to generate digest')
            }), 400
            
    except Exception as e:
        current_app.logger.error(f'API digest generation error: {str(e)}')
        return jsonify({
            'status': 'error',
            'error_type': 'internal_error',
            'message': 'An unexpected error occurred'
        }), 500


@api_bp.route('/digest/<int:digest_id>', methods=['GET'])
@api_login_required
def get_digest(digest_id):
    """
    Retrieve a specific digest
    
    Args:
        digest_id: ID of the digest to retrieve
        
    Returns:
        JSON response with digest data
        
    Status codes:
        200: Success
        401: Unauthorized
        403: Forbidden (not user's digest)
        404: Digest not found
    """
    digest = DigestRecord.query.get_or_404(digest_id)
    
    # Ensure user can only access their own digests
    if digest.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'Access denied'
        }), 403
    
    return jsonify({
        'status': 'success',
        'digest': {
            'id': digest.id,
            'generated_at': digest.generated_at.isoformat(),
            'email_count': digest.email_count,
            'meeting_count': digest.meeting_count,
            'data': digest.digest_data,
            'data_source': digest.data_source,
            'processing_time': digest.processing_time
        }
    })


@api_bp.route('/digest/history', methods=['GET'])
@api_login_required
def digest_history():
    """
    Get user's digest history
    
    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 10, max: 50)
        
    Returns:
        JSON response with paginated digest history
        
    Status codes:
        200: Success
        401: Unauthorized
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    pagination = DigestRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(
        DigestRecord.generated_at.desc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    digests = [{
        'id': d.id,
        'generated_at': d.generated_at.isoformat(),
        'email_count': d.email_count,
        'meeting_count': d.meeting_count,
        'data_source': d.data_source,
        'success': d.error_message is None
    } for d in pagination.items]
    
    return jsonify({
        'status': 'success',
        'digests': digests,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })


@api_bp.route('/digest/status', methods=['GET'])
@api_login_required
def digest_status():
    """
    Get current digest generation status for user
    
    Returns:
        JSON response with usage status
        
    Status codes:
        200: Success
        401: Unauthorized
    """
    today = date.today()
    daily_usage = DailyUsage.query.filter_by(
        user_id=current_user.id,
        usage_date=today
    ).first()
    
    can_generate = not daily_usage or daily_usage.digest_count < 1
    remaining = 1 - (daily_usage.digest_count if daily_usage else 0)
    
    # Get last digest
    last_digest = DigestRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(
        DigestRecord.generated_at.desc()
    ).first()
    
    return jsonify({
        'status': 'success',
        'usage': {
            'can_generate': can_generate,
            'daily_limit': 1,
            'used_today': daily_usage.digest_count if daily_usage else 0,
            'remaining': max(0, remaining),
            'reset_time': 'midnight'
        },
        'last_digest': {
            'id': last_digest.id,
            'generated_at': last_digest.generated_at.isoformat()
        } if last_digest else None
    })


@api_bp.route('/digest/test', methods=['GET'])
@api_login_required
def test_digest():
    """
    Generate a test digest without counting against daily limit
    
    Returns:
        JSON response with test digest data
        
    Status codes:
        200: Success
        401: Unauthorized
    """
    from app.services.test_data_service import TestDataService
    from app.services.digest_generator import StructuredDigestGenerator
    
    try:
        # Get test data
        test_service = TestDataService()
        emails, calendar_events = test_service.get_sample_data()
        
        # Generate test digest
        generator = StructuredDigestGenerator()
        digest_data = generator.generate_digest(
            emails,
            calendar_events,
            current_user.full_name
        )
        
        return jsonify({
            'status': 'success',
            'test_mode': True,
            'digest': digest_data
        })
        
    except Exception as e:
        current_app.logger.error(f'Test digest generation error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate test digest'
        }), 500
