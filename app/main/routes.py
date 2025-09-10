"""
Main application routes

This module contains the main application routes including
dashboard, settings, and core functionality.
"""
from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.main import main_bp
from app.main.forms import SettingsForm
from app.models import UserSettings, DailyUsage, DigestRecord
from app.services.digest_service import DigestService
from app.services.user_service import UserService
from app.utils.decorators import check_daily_limit


@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard with 'How's My Day' button"""
    # Get user settings
    settings = current_user.settings
    if not settings:
        # Create default settings if not exists
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    
    # Check if user can generate digest today
    today = date.today()
    daily_usage = DailyUsage.query.filter_by(
        user_id=current_user.id,
        usage_date=today
    ).first()
    
    can_generate = not daily_usage or daily_usage.digest_count < 1
    
    # Get recent digests
    recent_digests = DigestRecord.query.filter_by(
        user_id=current_user.id,
        error_message=None
    ).order_by(DigestRecord.generated_at.desc()).limit(5).all()
    
    # Get usage statistics
    total_digests = DigestRecord.query.filter_by(user_id=current_user.id).count()
    
    context = {
        'settings': settings.to_dict(),
        'can_generate': can_generate,
        'recent_digests': recent_digests,
        'total_digests': total_digests,
        'microsoft_linked': current_user.has_microsoft_linked,
        'next_available': 'Tomorrow' if not can_generate else 'Now'
    }
    
    return render_template('main/dashboard.html', **context)


@main_bp.route('/generate-digest', methods=['POST'])
@login_required
@check_daily_limit
def generate_digest():
    """Generate daily digest (How's My Day button)"""
    try:
        digest_service = DigestService()
        result = digest_service.generate_digest_for_user(current_user.id)
        
        if result['status'] == 'success':
            flash('Your daily digest has been generated successfully!', 'success')
            return jsonify({
                'status': 'success',
                'digest_id': result['digest_id'],
                'redirect_url': url_for('main.view_digest', digest_id=result['digest_id'])
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', 'Failed to generate digest')
            }), 400
            
    except Exception as e:
        current_app.logger.error(f'Digest generation error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while generating your digest. Please try again.'
        }), 500


@main_bp.route('/digest/<int:digest_id>')
@login_required
def view_digest(digest_id):
    """View a specific digest"""
    digest = DigestRecord.query.get_or_404(digest_id)
    
    # Ensure user can only view their own digests
    if digest.user_id != current_user.id:
        flash('You do not have permission to view this digest.', 'danger')
        return redirect(url_for('main.index'))
    
    # Extract digest data if it exists
    digest_data = digest.digest_data or {}
    
    # Check if we have the formatted HTML version
    if 'sections' in digest_data and 'metadata' in digest_data:
        # We have structured data, let's format it
        from app.services.digest_generator import StructuredDigestGenerator
        generator = StructuredDigestGenerator()
        digest.digest_data = generator.format_digest_html(digest_data)
    
    # Pass both the digest record and extracted data
    context = {
        'digest': digest,
        'digest_data': digest_data,
        'current_user': current_user
    }
    
    return render_template('main/digest.html', **context)


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page"""
    # Get or create user settings
    user_settings = current_user.settings
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()
    
    form = SettingsForm(obj=user_settings)
    
    if form.validate_on_submit():
        try:
            # Update settings
            settings_data = {
                'digest_time': form.digest_time.data,
                'timezone': form.timezone.data,
                'privacy_mode': form.privacy_mode.data,
                'working_hours_start': form.working_hours_start.data,
                'working_hours_end': form.working_hours_end.data,
                'email_notifications': form.email_notifications.data,
                'digest_format': form.digest_format.data
            }
            
            user_settings.update_settings(settings_data)
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('main.settings'))
            
        except Exception as e:
            current_app.logger.error(f'Settings update error: {str(e)}')
            flash('Error updating settings. Please try again.', 'danger')
    
    # Pre-populate form with current settings
    if not form.is_submitted():
        settings_dict = user_settings.to_dict()
        for field in form:
            if field.name in settings_dict:
                field.data = settings_dict[field.name]
    
    context = {
        'form': form,
        'microsoft_linked': current_user.has_microsoft_linked,
        'microsoft_email': current_user.microsoft_account_email,
        'settings': user_settings.to_dict()
    }
    
    return render_template('main/settings.html', **context)


@main_bp.route('/api/usage-status')
@login_required
def usage_status():
    """Get current usage status for the user"""
    today = date.today()
    daily_usage = DailyUsage.query.filter_by(
        user_id=current_user.id,
        usage_date=today
    ).first()
    
    can_generate = not daily_usage or daily_usage.digest_count < 1
    
    if can_generate:
        message = "Ready to generate your daily digest!"
    else:
        message = "You've already generated today's digest. Please try again tomorrow."
    
    return jsonify({
        'can_generate': can_generate,
        'message': message,
        'digest_count': daily_usage.digest_count if daily_usage else 0,
        'last_generation': daily_usage.last_generation_at.isoformat() if daily_usage and daily_usage.last_generation_at else None,
        'next_available': 'Tomorrow at midnight' if not can_generate else 'Now'
    })


@main_bp.route('/privacy-test')
@login_required
def privacy_test():
    """Test privacy/PII redaction functionality"""
    from app.services.privacy_service import PrivacyService
    
    # Sample email for testing
    sample_email = {
        'subject': 'Meeting with John Smith about Project Alpha',
        'bodyPreview': 'Hi Sarah, Can you call me at 555-123-4567? We need to discuss the contract with ACME Corp. My email is john.smith@company.com. Best regards, John',
        'from': {'emailAddress': {'name': 'John Smith', 'address': 'john.smith@company.com'}},
        'receivedDateTime': datetime.utcnow().isoformat()
    }
    
    privacy_service = PrivacyService()
    redacted_email, redaction_map = privacy_service.redact_email(sample_email)
    reconstructed = privacy_service.reconstruct_email(redacted_email, redaction_map)
    
    return jsonify({
        'original': sample_email,
        'redacted': redacted_email,
        'reconstructed': reconstructed,
        'redaction_map': redaction_map,
        'redaction_summary': privacy_service.get_redaction_summary(redaction_map)
    })


@main_bp.route('/help')
def help():
    """Help and documentation page"""
    return render_template('main/help.html')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html', version=current_app.config.get('APP_VERSION'))
