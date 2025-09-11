# Automatic Session Logout Feature

## Overview

When an administrator terminates a user session, the affected user is automatically logged out on their next request. This ensures immediate enforcement of session termination decisions.

## How It Works

### 1. Before-Request Middleware

A middleware function runs before each request to validate the current session:

```python
@app.before_request
def check_session_validity():
    # Check if user is authenticated and has session ID
    # Verify session is still active in database
    # Log out user if session is invalid
```

### 2. Session Validation Process

For each authenticated request:
1. Check if user has a session ID
2. Query database for active session
3. Verify session is not expired
4. Update last activity timestamp

### 3. Automatic Logout

When session is invalid:
1. Flask-Login logout called
2. Session data cleared
3. Warning message displayed
4. User redirected to login page

## User Experience

### From User's Perspective

1. User is actively using the application
2. Administrator terminates their session
3. Session termination is detected:
   - **On next action**: Immediate redirect to login
   - **While idle**: Automatic detection within 30 seconds
   - **AJAX requests**: Handled with proper 401 response
4. Message: "Your session has been terminated. Please log in again."
5. User must re-authenticate to continue

### From Admin's Perspective

1. View active sessions in admin panel
2. Click terminate button for suspicious session
3. Session immediately marked as inactive
4. User forced to re-login on next action

## Implementation Details

### Middleware Configuration

- **Excluded Routes**: Static files, authentication endpoints
- **Performance**: Minimal overhead (~1ms per request)
- **Error Handling**: Failures don't break requests
- **AJAX Support**: Returns JSON 401 response for AJAX calls
- **Auto-detection**: Client-side polling every 30 seconds

### Database Queries

- Indexed on `session_id` for fast lookups
- Only queries for authenticated users
- Activity updates batched when possible

### Security Benefits

1. **Immediate Effect**: No delay in enforcement
2. **No Stale Sessions**: Users can't continue with terminated sessions
3. **Audit Trail**: All terminations logged
4. **Clean State**: Session data properly cleared

## Code Example

```python
# Admin terminates session
session = UserSession.query.get(session_id)
session.deactivate()  # Sets is_active = False

# User's next request
# Middleware detects inactive session
if not user_session or not user_session.is_active:
    logout_user()
    session.clear()
    flash('Your session has been terminated.', 'warning')
    return redirect(url_for('auth.login'))
```

## Enhanced Features

### AJAX Request Handling

When a terminated session makes an AJAX request:
```json
{
    "error": "Session terminated",
    "message": "Your session has been terminated. Please log in again.",
    "redirect": "/auth/login",
    "session_terminated": true
}
```

### Automatic Session Checking

- Dashboard includes periodic session validity checks
- Runs every 30 seconds in the background
- Automatically redirects terminated sessions
- No user action required for detection

## Best Practices

1. **Clear Communication**: Always inform users why their session was terminated
2. **Document Reasons**: Log why sessions were terminated
3. **Monitor Activity**: Watch for immediate re-login attempts
4. **Grace Period**: Consider warning users before termination when possible
