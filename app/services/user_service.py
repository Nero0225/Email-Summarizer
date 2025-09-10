"""
User Service

This module handles user-related business logic including
user creation, authentication, and management.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from flask import current_app
from sqlalchemy import or_
from app import db
from app.models import User, UserStatus, UserRole, UserSettings


class UserService:
    """Service class for user management operations"""
    
    def create_user(self, username: str, email: str, full_name: str, 
                   password: str = None, is_admin: bool = False,
                   auto_approve: bool = False, 
                   microsoft_account_email: str = None) -> User:
        """
        Create a new user account
        
        Args:
            username: User's username
            email: User's email address
            full_name: User's full name
            password: Plain text password (optional for OAuth users)
            is_admin: Whether user should be admin
            auto_approve: Whether to auto-approve account
            microsoft_account_email: Microsoft account email for OAuth users
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username or email already exists
        """
        # Check if username exists
        if User.query.filter_by(username=username.lower()).first():
            raise ValueError('Username already exists')
        
        # Check if email exists
        if User.query.filter_by(email=email.lower()).first():
            raise ValueError('Email already registered')
        
        # Create user
        user = User(
            username=username.lower(),
            email=email.lower(),
            full_name=full_name,
            role=UserRole.ADMIN if is_admin else UserRole.USER,
            status=UserStatus.APPROVED if auto_approve else UserStatus.PENDING
        )
        
        # Set password only if provided (OAuth users may not have passwords)
        if password:
            user.set_password(password)
        
        # Link Microsoft account if provided
        if microsoft_account_email:
            user.link_microsoft_account(microsoft_account_email)
        
        # Set approval timestamp if auto-approved
        if auto_approve:
            user.approved_at = datetime.utcnow()
        
        # Create default settings
        settings = UserSettings(user=user)
        
        # Save to database
        db.session.add(user)
        db.session.add(settings)
        db.session.commit()
        
        # Log user creation
        current_app.logger.info(f'User created: {username} ({email})')
        
        # TODO: Send welcome email
        if not auto_approve:
            self._send_pending_approval_email(user)
        
        return user
    
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/email and password
        
        Args:
            username_or_email: Username or email
            password: Plain text password
            
        Returns:
            User object if authenticated, None otherwise
        """
        # Find user by username or email
        user = User.query.filter(
            or_(
                User.username == username_or_email.lower(),
                User.email == username_or_email.lower()
            )
        ).first()
        
        if not user:
            return None
        
        # Check password
        if not user.check_password(password):
            return None
        
        # Check if account is approved
        if user.status != UserStatus.APPROVED:
            return None
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return User.query.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return User.query.filter_by(username=username.lower()).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return User.query.filter_by(email=email.lower()).first()
    
    def get_pending_users(self) -> List[User]:
        """Get all users pending approval"""
        return User.query.filter_by(
            status=UserStatus.PENDING
        ).order_by(User.created_at.asc()).all()
    
    def approve_user(self, user_id: int, admin_id: int) -> bool:
        """
        Approve a pending user
        
        Args:
            user_id: ID of user to approve
            admin_id: ID of admin approving
            
        Returns:
            True if successful, False otherwise
        """
        user = self.get_user_by_id(user_id)
        admin = self.get_user_by_id(admin_id)
        
        if not user or not admin:
            return False
        
        if user.status != UserStatus.PENDING:
            return False
        
        user.approve(admin)
        
        # Send approval email
        self._send_approval_email(user)
        
        current_app.logger.info(
            f'User {user.username} approved by admin {admin.username}'
        )
        
        return True
    
    def reject_user(self, user_id: int, admin_id: int, reason: str = None) -> bool:
        """
        Reject a pending user
        
        Args:
            user_id: ID of user to reject
            admin_id: ID of admin rejecting
            reason: Optional rejection reason
            
        Returns:
            True if successful, False otherwise
        """
        user = self.get_user_by_id(user_id)
        admin = self.get_user_by_id(admin_id)
        
        if not user or not admin:
            return False
        
        if user.status != UserStatus.PENDING:
            return False
        
        user.reject(admin)
        
        # Send rejection email
        self._send_rejection_email(user, reason)
        
        current_app.logger.info(
            f'User {user.username} rejected by admin {admin.username}'
        )
        
        return True
    
    def suspend_user(self, user_id: int, admin_id: int, reason: str = None) -> bool:
        """
        Suspend an active user
        
        Args:
            user_id: ID of user to suspend
            admin_id: ID of admin suspending
            reason: Optional suspension reason
            
        Returns:
            True if successful, False otherwise
        """
        user = self.get_user_by_id(user_id)
        admin = self.get_user_by_id(admin_id)
        
        if not user or not admin:
            return False
        
        if user.status != UserStatus.APPROVED:
            return False
        
        user.suspend()
        
        # Send suspension email
        self._send_suspension_email(user, reason)
        
        current_app.logger.info(
            f'User {user.username} suspended by admin {admin.username}'
        )
        
        return True
    
    def reactivate_user(self, user_id: int, admin_id: int) -> bool:
        """
        Reactivate a suspended user
        
        Args:
            user_id: ID of user to reactivate
            admin_id: ID of admin reactivating
            
        Returns:
            True if successful, False otherwise
        """
        user = self.get_user_by_id(user_id)
        admin = self.get_user_by_id(admin_id)
        
        if not user or not admin:
            return False
        
        if user.status != UserStatus.SUSPENDED:
            return False
        
        user.status = UserStatus.APPROVED
        db.session.commit()
        
        # Send reactivation email
        self._send_reactivation_email(user)
        
        current_app.logger.info(
            f'User {user.username} reactivated by admin {admin.username}'
        )
        
        return True
    
    def update_user_profile(self, user_id: int, **kwargs) -> bool:
        """
        Update user profile information
        
        Args:
            user_id: User ID
            **kwargs: Fields to update (full_name, email)
            
        Returns:
            True if successful, False otherwise
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Update allowed fields
        if 'full_name' in kwargs:
            user.full_name = kwargs['full_name']
        
        if 'email' in kwargs:
            # Check if email is already taken by another user
            existing = User.query.filter(
                User.email == kwargs['email'].lower(),
                User.id != user_id
            ).first()
            if existing:
                raise ValueError('Email already registered')
            user.email = kwargs['email'].lower()
        
        db.session.commit()
        return True
    
    def change_password(self, user_id: int, current_password: str, 
                       new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if successful, False if current password is wrong
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not user.check_password(current_password):
            return False
        
        # Set new password
        user.set_password(new_password)
        db.session.commit()
        
        # Send password change notification
        self._send_password_change_email(user)
        
        return True
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get user statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of user statistics
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        from app.models import DigestRecord, DailyUsage
        
        stats = {
            'total_digests': DigestRecord.query.filter_by(user_id=user_id).count(),
            'successful_digests': DigestRecord.query.filter_by(
                user_id=user_id, 
                error_message=None
            ).count(),
            'days_active': DailyUsage.query.filter_by(user_id=user_id).count(),
            'account_age_days': (datetime.utcnow() - user.created_at).days,
            'last_active': user.last_login
        }
        
        return stats
    
    # Email notification methods (stubs for now)
    def _send_pending_approval_email(self, user: User):
        """Send email notification for pending approval"""
        # TODO: Implement email sending
        pass
    
    def _send_approval_email(self, user: User):
        """Send email notification for account approval"""
        # TODO: Implement email sending
        pass
    
    def _send_rejection_email(self, user: User, reason: str = None):
        """Send email notification for account rejection"""
        # TODO: Implement email sending
        pass
    
    def _send_suspension_email(self, user: User, reason: str = None):
        """Send email notification for account suspension"""
        # TODO: Implement email sending
        pass
    
    def _send_reactivation_email(self, user: User):
        """Send email notification for account reactivation"""
        # TODO: Implement email sending
        pass
    
    def _send_password_change_email(self, user: User):
        """Send email notification for password change"""
        # TODO: Implement email sending
        pass
