# OAuth User Password Policy

## Overview

Users who register through Microsoft OAuth2 are automatically assigned a default password, allowing them to access their account through both Microsoft sign-in and traditional username/password login.

## Default Password

When a user registers using Microsoft OAuth:
- **Default Password**: `P@ssw0rd`
- **Username**: Derived from their email (e.g., john.doe@example.com → john.doe)
- **Email**: Their Microsoft account email

## Security Recommendations

### For New OAuth Users
1. After registration, users receive a notification about their default password
2. Users are strongly encouraged to change the default password immediately
3. Navigate to Settings → Account Security → Change Password

### Login Options

OAuth users can log in using:

1. **Microsoft Sign-In**
   - Click "Sign in with Microsoft" button
   - Authenticate with Microsoft credentials
   - No password required

2. **Traditional Login**
   - Username: Their username or email address
   - Password: Default `P@ssw0rd` or their updated password
   - Available from the standard login form

## Implementation Details

### Registration Flow
```python
# OAuth user creation with default password
user = user_service.create_user(
    username=username,
    email=microsoft_email,
    password='P@ssw0rd',  # Default password
    microsoft_account_email=microsoft_email,
    auto_approve=True
)
```

### User Notifications
- Success message: "Welcome [Name]! Your account has been created successfully."
- Security notice: "Your default password is: P@ssw0rd - Please change it in Settings for security."

### Password Change Access
- All users (OAuth and traditional) can change their password
- Located in Settings → Account Security
- Requires current password verification

## Security Considerations

### Advantages
- **Dual Access**: Users can access their account even if Microsoft OAuth is unavailable
- **Account Recovery**: Alternative login method if OAuth issues occur
- **Admin Access**: Administrators can reset passwords if needed
- **Flexibility**: Users choose their preferred login method

### Best Practices
1. **Immediate Change**: Users should change the default password upon first login
2. **Strong Password**: Encourage using unique, complex passwords
3. **Regular Updates**: Promote periodic password changes
4. **Security Education**: Inform users about password security

## User Experience

### First Login
1. Register with Microsoft OAuth
2. Account created with default password
3. Notification about default password displayed
4. User logs in (via Microsoft or traditional)
5. Prompted to change password for security

### Subsequent Logins
- Choose between Microsoft sign-in or username/password
- Both methods provide full account access
- Password can be changed anytime in Settings

## Administrator Information

### Managing OAuth Users
- OAuth users appear in user management with Microsoft email displayed
- Admins can reset passwords for OAuth users if needed
- User status and roles function identically for all users

### Identifying OAuth Users
- `has_microsoft_linked` property indicates OAuth registration
- `microsoft_account_email` contains their Microsoft email
- Password field is populated (not NULL)
