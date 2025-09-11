# Admin Settings Configuration

## Overview

Administrator accounts have a customized settings page that focuses on their administrative needs while removing unnecessary features that are only relevant to regular users.

## Key Differences for Admin Settings

### 1. Hidden Features

The following features are hidden from the admin settings page:

#### Microsoft 365 Connection
- **Reason**: Administrators don't need to connect their Microsoft 365 accounts to perform administrative functions
- **Benefits**: 
  - Reduces interface complexity
  - Prevents confusion about which features require Microsoft connection
  - Focuses on administrative tasks
  - Improves security by not requiring admin accounts to grant external permissions

### 2. Visible Features

Administrators still have access to:

#### Account Security
- Change password functionality
- Last password update information
- Security reminders

#### General Settings
- Timezone configuration
- Working hours
- Digest preferences (for testing purposes)
- Privacy mode toggle
- Email notification preferences
- Digest format selection

#### Account Information
- Username and email display
- Role badge showing "ADMIN"
- Member since date

## Implementation Details

### Template Logic

```jinja2
<!-- Microsoft 365 Connection -->
{% if not current_user.is_admin %}
<div class="card mb-4 fade-in">
    <!-- Microsoft connection UI -->
</div>
{% endif %}
```

### Backend Behavior

- Settings route remains unchanged
- All users (including admins) can access `/settings`
- Template handles visibility based on `current_user.is_admin`
- No special routing or permissions required

## User Experience

### Regular Users See:
1. Microsoft 365 Connection card
2. Account Security card
3. General Settings card
4. Account Information sidebar

### Administrators See:
1. ~~Microsoft 365 Connection card~~ (Hidden)
2. Account Security card
3. General Settings card
4. Account Information sidebar (with Admin badge)

## Best Practices

1. **Consistency**: Keep the same URL and route for all users
2. **Progressive Enhancement**: Hide features rather than disable them
3. **Clear Role Indication**: Show admin badge in account information
4. **Security**: Don't expose unnecessary external integrations to admin accounts

## Future Considerations

- Add admin-specific settings (e.g., system-wide defaults)
- Consider separate admin preferences page
- Add bulk user preference management
- System maintenance settings

## FAQ

**Q: Can admins still connect Microsoft 365 if needed?**
A: No, the interface is completely hidden. This is by design to keep admin accounts focused on administrative tasks.

**Q: What if an admin needs to test Microsoft integration?**
A: Admins should use a separate test account with regular user privileges for testing user features.

**Q: Are there any features admins can't access?**
A: Admins can't generate email digests or connect Microsoft accounts, but they have full access to all administrative features.
