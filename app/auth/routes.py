"""
Authentication routes

This module contains all authentication-related routes including
login, logout, registration, and Microsoft OAuth callbacks.
"""
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from app import db
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User, UserStatus, UserSettings, MicrosoftToken
from app.services.microsoft_service import MicrosoftService
from app.services.user_service import UserService


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == form.username.data.lower()) | 
            (User.email == form.username.data.lower())
        ).first()
        
        if user:
            # Check if this is an OAuth-only user
            if user.is_oauth_user:
                flash('This account uses Microsoft sign-in. Please use "Sign in with Microsoft" instead.', 'warning')
            elif user.check_password(form.password.data):
                if user.status == UserStatus.APPROVED:
                    login_user(user, remember=form.remember_me.data)
                    user.update_last_login()
                    
                    # Handle next page redirect
                    next_page = request.args.get('next')
                    if not next_page or urlparse(next_page).netloc != '':
                        # Redirect admin users to admin dashboard
                        if user.is_admin:
                            next_page = url_for('admin.dashboard')
                        else:
                            next_page = url_for('main.index')
                    
                    flash(f'Welcome back, {user.full_name}!', 'success')
                    return redirect(next_page)
                elif user.status == UserStatus.PENDING:
                    flash('Your account is pending approval. Please wait for an administrator to approve your account.', 'warning')
                elif user.status == UserStatus.REJECTED:
                    flash('Your account application was rejected. Please contact support for more information.', 'danger')
                elif user.status == UserStatus.SUSPENDED:
                    flash('Your account has been suspended. Please contact support.', 'danger')
            else:
                flash('Invalid username/email or password. Please try again.', 'danger')
        else:
            flash('Invalid username/email or password. Please try again.', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register')
def register():
    """User registration route - redirects to Microsoft OAuth"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))
    
    # Redirect to Microsoft OAuth for registration
    return redirect(url_for('auth.microsoft_register'))


@auth_bp.route('/microsoft/register')
def microsoft_register():
    """Initiate Microsoft OAuth2 registration/login"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))
    
    microsoft_service = MicrosoftService()
    auth_url = microsoft_service.get_auth_url()
    
    if auth_url:
        # Store registration flag in session
        session['microsoft_auth_type'] = 'register'
        return redirect(auth_url)
    else:
        flash(
            'Microsoft authentication is not configured. '
            'Please contact your administrator.',
            'danger'
        )
        return redirect(url_for('auth.login'))


@auth_bp.route('/microsoft/login')
def microsoft_login():
    """Initiate Microsoft OAuth2 login for account linking"""
    if not current_user.is_authenticated:
        flash('Please log in first to link your Microsoft account.', 'warning')
        return redirect(url_for('auth.login'))
    
    microsoft_service = MicrosoftService()
    auth_url = microsoft_service.get_auth_url()
    
    if auth_url:
        # Store user ID and auth type in session for callback
        session['linking_user_id'] = current_user.id
        session['microsoft_auth_type'] = 'link'
        return redirect(auth_url)
    else:
        flash(
            'Microsoft authentication is not configured. '
            'Please contact your administrator.',
            'danger'
        )
        return redirect(url_for('main.settings'))


@auth_bp.route('/callback')
def microsoft_callback():
    """Handle Microsoft OAuth2 callback for both registration and account linking"""
    # Get authorization code or error from query parameters
    auth_code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    # Get auth type from session
    auth_type = session.pop('microsoft_auth_type', None)
    linking_user_id = session.pop('linking_user_id', None)
    
    if not auth_type:
        flash('Session expired. Please try again.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Handle OAuth errors
    if error:
        error_msg = f'Microsoft authentication failed: {error}'
        if error_description:
            error_msg += f' - {error_description}'
        flash(error_msg, 'danger')
        return redirect(url_for('auth.login'))
    
    if not auth_code:
        flash('No authorization code received from Microsoft.', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        microsoft_service = MicrosoftService()
        token_result = microsoft_service.get_token_from_code(auth_code)
        
        if token_result and 'access_token' in token_result:
            # Get Microsoft user profile
            profile = microsoft_service.get_user_profile(token_result['access_token'])
            microsoft_email = profile.get('mail') or profile.get('userPrincipalName')
            display_name = profile.get('displayName', '')
            
            if microsoft_email:
                # Calculate token expiration
                expires_at = datetime.utcnow() + timedelta(
                    seconds=token_result.get('expires_in', 3600)
                )
                
                if auth_type == 'register':
                    # Handle registration flow
                    try:
                        # Check if user already exists with this email
                        existing_user = User.query.filter_by(email=microsoft_email.lower()).first()
                        if existing_user:
                            # User already exists - check if they have Microsoft linked
                            if existing_user.microsoft_account_email:
                                # Already has Microsoft linked, just log them in
                                login_user(existing_user, remember=True)
                                existing_user.update_last_login()
                                flash(f'Welcome back, {existing_user.full_name}!', 'success')
                                
                                # Redirect based on role
                                if existing_user.is_admin:
                                    return redirect(url_for('admin.dashboard'))
                                else:
                                    return redirect(url_for('main.index'))
                            else:
                                # User exists but no Microsoft account linked
                                flash('An account with this email already exists. Please log in to link your Microsoft account.', 'info')
                                return redirect(url_for('auth.login'))
                        
                        # Create username from email
                        username = microsoft_email.split('@')[0].lower()
                        # Ensure username is unique
                        base_username = username
                        counter = 1
                        while User.query.filter_by(username=username).first():
                            username = f"{base_username}{counter}"
                            counter += 1
                        
                        # Check if this is an admin email domain
                        admin_domains = current_app.config.get('ADMIN_EMAIL_DOMAINS', ['admin.com'])
                        is_admin = any(microsoft_email.lower().endswith(f'@{domain}') for domain in admin_domains)
                        
                        # Create new user
                        user_service = UserService()
                        user = user_service.create_user(
                            username=username,
                            full_name=display_name or username,
                            email=microsoft_email.lower(),
                            password=None,  # No password for OAuth users
                            microsoft_account_email=microsoft_email,
                            is_admin=is_admin,
                            auto_approve=True  # Auto-approve Microsoft OAuth users
                        )
                        
                        try:
                            # Store tokens
                            token_record = MicrosoftToken(
                                user_id=user.id,
                                access_token=token_result['access_token'],
                                refresh_token=token_result.get('refresh_token'),
                                token_expires_at=expires_at,
                                scope=' '.join(microsoft_service.scopes)
                            )
                            db.session.add(token_record)
                            
                            # Update user settings to use real data (settings already created by user_service)
                            if user.settings:
                                user.settings.update_setting('use_test_data', False)
                            
                            db.session.commit()
                            
                            # Log the user in
                            login_user(user, remember=True)
                            flash(f'Welcome {display_name}! Your account has been created successfully.', 'success')
                            
                            # Redirect based on role
                            if user.is_admin:
                                return redirect(url_for('admin.dashboard'))
                            else:
                                return redirect(url_for('main.index'))
                                
                        except Exception as e:
                            # Rollback user creation if token storage fails
                            db.session.rollback()
                            # Try to clean up the created user
                            if user and user.id:
                                User.query.filter_by(id=user.id).delete()
                                db.session.commit()
                            raise e
                            
                    except ValueError as e:
                        # Handle user creation errors (duplicate username/email)
                        current_app.logger.error(f'OAuth registration error: {str(e)}')
                        flash('Registration failed. Please try again or contact support.', 'danger')
                        return redirect(url_for('auth.login'))
                    except Exception as e:
                        # Handle any other errors
                        db.session.rollback()
                        current_app.logger.error(f'Unexpected OAuth registration error: {str(e)}')
                        flash('An unexpected error occurred. Please try again later.', 'danger')
                        return redirect(url_for('auth.login'))
                
                elif auth_type == 'link' and linking_user_id:
                    # Handle account linking flow
                    user = User.query.get(linking_user_id)
                    if user:
                        user.link_microsoft_account(microsoft_email)
                        
                        # Store or update tokens
                        if user.microsoft_tokens:
                            user.microsoft_tokens.update_tokens(
                                access_token=token_result['access_token'],
                                refresh_token=token_result.get('refresh_token'),
                                expires_at=expires_at,
                                scope=' '.join(microsoft_service.scopes)
                            )
                        else:
                            token_record = MicrosoftToken(
                                user_id=user.id,
                                access_token=token_result['access_token'],
                                refresh_token=token_result.get('refresh_token'),
                                token_expires_at=expires_at,
                                scope=' '.join(microsoft_service.scopes)
                            )
                            db.session.add(token_record)
                            db.session.commit()
                        
                        # Update user settings to use real data
                        if user.settings:
                            user.settings.update_setting('use_test_data', False)
                        
                        flash(
                            f'Successfully linked Microsoft 365 account ({microsoft_email})!',
                            'success'
                        )
                        return redirect(url_for('main.settings'))
                    else:
                        flash('User not found. Please try again.', 'danger')
                        return redirect(url_for('auth.login'))
                else:
                    flash('Invalid authentication type.', 'danger')
                    return redirect(url_for('auth.login'))
            else:
                flash('Could not retrieve email from Microsoft profile.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            error_msg = 'Failed to obtain access token from Microsoft.'
            if token_result and 'error_description' in token_result:
                error_msg += f" {token_result['error_description']}"
            flash(error_msg, 'danger')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        current_app.logger.error(f'Microsoft auth callback error: {str(e)}')
        flash(f'Microsoft authentication error: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/microsoft/unlink')
def microsoft_unlink():
    """Unlink Microsoft account"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    try:
        current_user.unlink_microsoft_account()
        
        # Switch back to test data mode
        if current_user.settings:
            current_user.settings.update_setting('use_test_data', True)
        
        flash(
            'Successfully unlinked Microsoft 365 account. '
            'Your digest will now use test data.',
            'success'
        )
    except Exception as e:
        current_app.logger.error(f'Error unlinking Microsoft account: {str(e)}')
        flash('Error unlinking Microsoft account. Please try again.', 'danger')
    
    return redirect(url_for('main.settings'))
