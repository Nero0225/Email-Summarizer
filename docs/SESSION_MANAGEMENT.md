# Session Management for Administrators

## Overview

The session management feature allows administrators to monitor and control active user sessions in the Email Summarizer application. This provides enhanced security and user management capabilities.

## Features

### 1. Session Tracking

Every user login creates a session record that tracks:
- **Session ID**: Unique identifier for the session
- **User**: The authenticated user
- **IP Address**: Client IP address
- **User Agent**: Browser/client information
- **Login Time**: When the session started
- **Last Activity**: Most recent activity timestamp
- **Duration**: How long the session has been active
- **Expiration**: 24-hour automatic expiration

### 2. Admin Dashboard Integration

Access session management from:
- Admin Dashboard → Quick Actions → Manage Sessions
- Direct URL: `/admin/sessions`

### 3. Session Statistics

The session management page displays:
- Total active sessions
- Number of unique users online
- Session duration policy (24 hours)

### 4. Active Sessions Table

View all active sessions with:
- User information (with admin badges)
- IP addresses
- Browser/agent details (truncated with tooltip)
- Login times
- Last activity
- Session duration
- Terminate button for each session

### 5. Search and Filter

- Search by username or email
- Real-time filtering of active sessions
- Clear search functionality

### 6. Session Termination

Administrators can:
- **Terminate Individual Session**: End a specific user session
- **Terminate All User Sessions**: End all sessions for a specific user
- **Automatic Cleanup**: Expired sessions are automatically removed

When a session is terminated:
- Session marked as inactive in database
- User automatically logged out on next request
- Flash message: "Your session has been terminated. Please log in again."
- User redirected to login page
- No ability to continue using the terminated session

### 7. Recent Login Activity

View login history for the last 24 hours:
- Login timestamps
- User identification
- IP addresses
- Session status (Active/Ended)

## Implementation Details

### Database Model
```python
class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    session_id = db.Column(db.String(255), unique=True)
    ip_address = db.Column(db.String(45))  # Supports IPv6
    user_agent = db.Column(db.String(255))
    login_at = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
```

### Session Creation
Sessions are created automatically when users:
- Login with username/password
- Login with Microsoft OAuth
- Register new accounts

### Session Deactivation
Sessions are deactivated when:
- User logs out
- Admin terminates the session
- Session expires (24 hours)
- User's all sessions are terminated

## Security Benefits

1. **Audit Trail**: Track all user logins with timestamps and IPs
2. **Force Logout**: Terminate suspicious or unauthorized sessions
3. **Multi-Device Management**: See and control user sessions across devices
4. **IP Tracking**: Identify unusual login locations
5. **Activity Monitoring**: Track last activity for inactive sessions

## Usage Scenarios

### Suspicious Activity
1. Admin notices unusual IP address
2. Reviews user agent information
3. Terminates suspicious session
4. User must re-authenticate

### Account Compromise
1. User reports potential compromise
2. Admin terminates all user sessions
3. User changes password
4. Fresh login required

### Maintenance
1. Before system updates
2. Terminate all active sessions
3. Users re-authenticate after update

## Best Practices

1. **Regular Monitoring**: Check active sessions periodically
2. **Investigate Anomalies**: Look for unusual IPs or multiple sessions
3. **Document Actions**: Log reasons for session terminations
4. **User Communication**: Inform users when sessions are terminated
5. **Cleanup Policy**: Expired sessions auto-cleanup maintains performance

## Technical Notes

- Sessions use secure random tokens (32 bytes, URL-safe)
- IP addresses support both IPv4 and IPv6
- User agents are limited to 255 characters
- Session data stored in Flask session (server-side)
- Database cascade deletes sessions when users are removed
- Before-request middleware validates sessions on each request
- Last activity automatically updated for active sessions
- Static files and authentication routes excluded from checks
