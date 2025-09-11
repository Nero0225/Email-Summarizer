# Password Management

## Overview

Users with traditional login accounts can change their passwords through the settings interface. This feature enhances account security by allowing users to regularly update their credentials.

## Features

### 1. Password Change for Traditional Users

Users who registered with username/password (not OAuth) can:
- Access password change from Settings page
- Update their password with proper validation
- View when they last updated their password

### 2. OAuth User Protection

Users who registered via Microsoft OAuth:
- Cannot change passwords (they don't have one)
- See an informational message explaining their security is managed by Microsoft
- Prevents confusion about password management

### 3. Security Requirements

Password change enforces:
- **Current Password Verification**: Must enter correct current password
- **Minimum Length**: New password must be at least 8 characters
- **Confirmation Match**: New password and confirmation must match
- **Secure Storage**: Passwords are hashed using bcrypt

## User Interface

### Settings Page - Account Security Section

For traditional users:
```
Account Security
Keep your account secure by regularly updating your password.
Last password update: [Date]
[Change Password Button]
```

For OAuth users:
```
Account Security
Your account uses Microsoft sign-in for authentication.
Password management is not available for Microsoft sign-in accounts.
```

### Change Password Page

Form fields:
1. Current Password (required)
2. New Password (min 8 chars)
3. Confirm New Password (must match)

Security tips displayed:
- Use a unique password
- Include mix of characters
- Consider password manager

## Implementation Details

### Route
```python
@main_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    # Checks if user is OAuth-only
    # Validates current password
    # Updates password hash
```

### Form Validation
```python
class PasswordChangeForm(FlaskForm):
    current_password = PasswordField(required)
    new_password = PasswordField(min_length=8)
    confirm_password = PasswordField(must_match_new_password)
```

### Security Checks
1. **Authentication**: User must be logged in
2. **Authorization**: Only non-OAuth users can access
3. **Verification**: Current password must be correct
4. **Validation**: New password meets requirements

## User Flow

### Traditional User
1. Navigate to Settings
2. See "Account Security" section
3. Click "Change Password"
4. Enter current and new passwords
5. Submit form
6. Receive confirmation message
7. Redirected to Settings

### OAuth User
1. Navigate to Settings
2. See "Account Security" section
3. Read message about Microsoft authentication
4. No password change option available

## Benefits

- **Security**: Regular password updates reduce breach risk
- **Control**: Users manage their own security
- **Clarity**: Clear distinction between auth methods
- **Validation**: Prevents weak passwords
- **Audit**: Tracks last password change date

## Error Handling

- **Incorrect Current Password**: Clear error message
- **Password Too Short**: Validation message
- **Passwords Don't Match**: Inline error
- **Database Error**: Graceful failure with rollback
