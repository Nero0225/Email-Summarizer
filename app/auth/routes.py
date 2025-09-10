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
        
        if user and user.check_password(form.password.data):
            if user.status == UserStatus.APPROVED:
                login_user(user, remember=form.remember_me.data)
                user.update_last_login()
                
                # Handle next page redirect
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
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
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user_service = UserService()
            user = user_service.create_user(
                username=form.username.data.strip().lower(),
                full_name=form.full_name.data.strip(),
                email=form.email.data.strip().lower(),
                password=form.password.data
            )
            
            flash(
                'Your account has been created successfully! '
                'Please wait for an administrator to approve your account before you can log in.',
                'success'
            )
            return redirect(url_for('auth.login'))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            current_app.logger.error(f'Registration error: {str(e)}')
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/microsoft/login')
def microsoft_login():
    """Initiate Microsoft OAuth2 login"""
    if not current_user.is_authenticated:
        flash('Please log in first to link your Microsoft account.', 'warning')
        return redirect(url_for('auth.login'))
    
    microsoft_service = MicrosoftService()
    auth_url = microsoft_service.get_auth_url()
    
    if auth_url:
        # Store user ID in session for callback
        session['linking_user_id'] = current_user.id
        return redirect(auth_url)
    else:
        flash(
            'Microsoft authentication is not configured. '
            'Please contact your administrator.',
            'danger'
        )
        return redirect(url_for('main.settings'))


@auth_bp.route('/microsoft/callback')
def microsoft_callback():
    """Handle Microsoft OAuth2 callback"""
    # Get authorization code or error from query parameters
    auth_code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    # Get the user who is linking their account
    linking_user_id = session.pop('linking_user_id', None)
    if not linking_user_id:
        flash('Session expired. Please try linking your Microsoft account again.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Handle OAuth errors
    if error:
        error_msg = f'Microsoft authentication failed: {error}'
        if error_description:
            error_msg += f' - {error_description}'
        flash(error_msg, 'danger')
        return redirect(url_for('main.settings'))
    
    if not auth_code:
        flash('No authorization code received from Microsoft.', 'danger')
        return redirect(url_for('main.settings'))
    
    try:
        microsoft_service = MicrosoftService()
        token_result = microsoft_service.get_token_from_code(auth_code)
        
        if token_result and 'access_token' in token_result:
            # Get Microsoft user profile
            profile = microsoft_service.get_user_profile(token_result['access_token'])
            microsoft_email = profile.get('mail') or profile.get('userPrincipalName')
            
            if microsoft_email:
                # Get user and link Microsoft account
                user = User.query.get(linking_user_id)
                if user:
                    user.link_microsoft_account(microsoft_email)
                    
                    # Store or update tokens
                    expires_at = datetime.utcnow() + timedelta(
                        seconds=token_result.get('expires_in', 3600)
                    )
                    
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
                else:
                    flash('User not found. Please try again.', 'danger')
            else:
                flash('Could not retrieve email from Microsoft profile.', 'danger')
        else:
            error_msg = 'Failed to obtain access token from Microsoft.'
            if token_result and 'error_description' in token_result:
                error_msg += f" {token_result['error_description']}"
            flash(error_msg, 'danger')
            
    except Exception as e:
        current_app.logger.error(f'Microsoft auth callback error: {str(e)}')
        flash(f'Microsoft authentication error: {str(e)}', 'danger')
    
    return redirect(url_for('main.settings'))


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
