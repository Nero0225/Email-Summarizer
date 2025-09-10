"""
Admin routes

This module contains all admin-related routes for user management,
system monitoring, and configuration.
"""
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.admin import admin_bp
from app.models import User, UserStatus, UserRole, DigestRecord, DailyUsage
from app.utils.decorators import admin_required
from app.services.user_service import UserService


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with system overview"""
    # Get system statistics
    stats = {
        'total_users': User.query.count(),
        'approved_users': User.query.filter_by(status=UserStatus.APPROVED).count(),
        'pending_users': User.query.filter_by(status=UserStatus.PENDING).count(),
        'suspended_users': User.query.filter_by(status=UserStatus.SUSPENDED).count(),
        'linked_users': User.query.filter(User.microsoft_account_email.isnot(None)).count(),
        'total_digests': DigestRecord.query.count(),
        'digests_today': DigestRecord.query.filter(
            func.date(DigestRecord.generated_at) == datetime.today().date()
        ).count()
    }
    
    # Get pending users for approval
    pending_users = User.query.filter_by(status=UserStatus.PENDING)\
        .order_by(User.created_at.asc()).limit(10).all()
    
    # Get recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_digests = DigestRecord.query.order_by(DigestRecord.generated_at.desc()).limit(5).all()
    
    # Get system health metrics
    health = {
        'database': 'healthy',
        'microsoft_api': 'configured' if current_app.config.get('AZURE_CLIENT_ID') else 'not configured',
        'openai_api': 'configured' if current_app.config.get('OPENAI_API_KEY') else 'not configured'
    }
    
    context = {
        'stats': stats,
        'pending_users': pending_users,
        'recent_users': recent_users,
        'recent_digests': recent_digests,
        'health': health
    }
    
    return render_template('admin/dashboard.html', **context)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    # Build query
    query = User.query
    
    # Apply filters
    if status_filter != 'all':
        try:
            status = UserStatus(status_filter)
            query = query.filter_by(status=status)
        except ValueError:
            pass
    
    if search_query:
        query = query.filter(
            (User.username.contains(search_query)) |
            (User.email.contains(search_query)) |
            (User.full_name.contains(search_query))
        )
    
    # Order and paginate
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    context = {
        'users': pagination.items,
        'pagination': pagination,
        'status_filter': status_filter,
        'search_query': search_query,
        'statuses': [status.value for status in UserStatus]
    }
    
    return render_template('admin/users.html', **context)


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View detailed user information"""
    user = User.query.get_or_404(user_id)
    
    # Get user's digest history
    digests = DigestRecord.query.filter_by(user_id=user_id)\
        .order_by(DigestRecord.generated_at.desc()).limit(10).all()
    
    # Get user's daily usage
    usage_stats = db.session.query(
        func.count(DailyUsage.id).label('days_used'),
        func.sum(DailyUsage.digest_count).label('total_digests')
    ).filter_by(user_id=user_id).first()
    
    context = {
        'user': user,
        'digests': digests,
        'usage_stats': usage_stats
    }
    
    return render_template('admin/user_detail.html', **context)


@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    """Approve a pending user"""
    user = User.query.get_or_404(user_id)
    
    if user.status != UserStatus.PENDING:
        flash(f'User {user.username} is not in pending status.', 'warning')
        return redirect(url_for('admin.users'))
    
    try:
        user.approve(current_user)
        flash(f'User {user.username} has been approved successfully.', 'success')
        
        # TODO: Send approval email notification
        
    except Exception as e:
        current_app.logger.error(f'Error approving user {user_id}: {str(e)}')
        flash('Error approving user. Please try again.', 'danger')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    """Reject a pending user"""
    user = User.query.get_or_404(user_id)
    
    if user.status != UserStatus.PENDING:
        flash(f'User {user.username} is not in pending status.', 'warning')
        return redirect(url_for('admin.users'))
    
    try:
        user.reject(current_user)
        flash(f'User {user.username} has been rejected.', 'info')
        
        # TODO: Send rejection email notification
        
    except Exception as e:
        current_app.logger.error(f'Error rejecting user {user_id}: {str(e)}')
        flash('Error rejecting user. Please try again.', 'danger')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@login_required
@admin_required
def suspend_user(user_id):
    """Suspend an active user"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot suspend your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    if user.status != UserStatus.APPROVED:
        flash(f'User {user.username} is not active.', 'warning')
        return redirect(url_for('admin.users'))
    
    try:
        user.suspend()
        flash(f'User {user.username} has been suspended.', 'warning')
        
        # TODO: Send suspension email notification
        
    except Exception as e:
        current_app.logger.error(f'Error suspending user {user_id}: {str(e)}')
        flash('Error suspending user. Please try again.', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_user(user_id):
    """Reactivate a suspended user"""
    user = User.query.get_or_404(user_id)
    
    if user.status != UserStatus.SUSPENDED:
        flash(f'User {user.username} is not suspended.', 'warning')
        return redirect(url_for('admin.users'))
    
    try:
        user.status = UserStatus.APPROVED
        db.session.commit()
        flash(f'User {user.username} has been reactivated.', 'success')
        
    except Exception as e:
        current_app.logger.error(f'Error activating user {user_id}: {str(e)}')
        flash('Error activating user. Please try again.', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/make-admin', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    """Promote user to admin role"""
    user = User.query.get_or_404(user_id)
    
    if user.role == UserRole.ADMIN:
        flash(f'User {user.username} is already an admin.', 'info')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    try:
        user.role = UserRole.ADMIN
        db.session.commit()
        flash(f'User {user.username} has been promoted to admin.', 'success')
        
    except Exception as e:
        current_app.logger.error(f'Error promoting user {user_id}: {str(e)}')
        flash('Error promoting user. Please try again.', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/remove-admin', methods=['POST'])
@login_required
@admin_required
def remove_admin(user_id):
    """Remove admin role from user"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot remove your own admin privileges.', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    # Check if this is the last admin
    admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
    if admin_count <= 1:
        flash('Cannot remove admin privileges. At least one admin user must exist.', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    try:
        user.role = UserRole.USER
        db.session.commit()
        flash(f'Admin privileges removed from user {user.username}.', 'info')
        
    except Exception as e:
        current_app.logger.error(f'Error demoting user {user_id}: {str(e)}')
        flash('Error removing admin privileges. Please try again.', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/system')
@login_required
@admin_required
def system():
    """System configuration and monitoring"""
    # Get configuration status
    config_status = {
        'azure_configured': bool(current_app.config.get('AZURE_CLIENT_ID')),
        'openai_configured': bool(current_app.config.get('OPENAI_API_KEY')),
        'email_configured': bool(current_app.config.get('MAIL_SERVER')),
        'database_type': current_app.config.get('SQLALCHEMY_DATABASE_URI', '').split(':')[0]
    }
    
    # Get usage statistics
    usage_stats = {
        'total_users': User.query.count(),
        'active_users_today': DailyUsage.query.filter(
            func.date(DailyUsage.usage_date) == datetime.today().date()
        ).distinct(DailyUsage.user_id).count(),
        'digests_today': DigestRecord.query.filter(
            func.date(DigestRecord.generated_at) == datetime.today().date()
        ).count(),
        'failed_digests_today': DigestRecord.query.filter(
            func.date(DigestRecord.generated_at) == datetime.today().date(),
            DigestRecord.error_message.isnot(None)
        ).count()
    }
    
    # Get performance metrics
    avg_processing_time = db.session.query(
        func.avg(DigestRecord.processing_time)
    ).filter(
        DigestRecord.processing_time.isnot(None),
        DigestRecord.error_message.is_(None)
    ).scalar() or 0
    
    performance_stats = {
        'avg_processing_time': round(avg_processing_time, 2),
        'database_size': 'N/A'  # Would need OS-specific implementation
    }
    
    context = {
        'config_status': config_status,
        'usage_stats': usage_stats,
        'performance_stats': performance_stats
    }
    
    return render_template('admin/system.html', **context)


@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    """View application logs"""
    # This is a simplified implementation
    # In production, you'd want to use a proper logging service
    
    try:
        log_file = 'logs/email_summarizer.log'
        lines = request.args.get('lines', 100, type=int)
        
        with open(log_file, 'r') as f:
            log_lines = f.readlines()[-lines:]
            
        logs = ''.join(log_lines)
        
    except FileNotFoundError:
        logs = 'Log file not found.'
    except Exception as e:
        logs = f'Error reading logs: {str(e)}'
    
    return render_template('admin/logs.html', logs=logs, lines=lines)
