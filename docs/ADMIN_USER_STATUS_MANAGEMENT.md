# Admin User Status Management

## Overview

Administrators can now easily change user status through the admin panel with a flexible dropdown interface and quick action buttons.

## Features

### 1. Status Change Dropdown (User Detail Page)

In the user detail page, administrators can:
- Select any valid status from a dropdown menu
- Change user status with a single click
- Current status is displayed and disabled in the dropdown
- Confirmation dialog prevents accidental changes

### 2. Quick Action Buttons (Users List)

The users list now includes contextual quick action buttons:
- **Pending Users**: Approve ✓ or Reject ✗ buttons
- **Approved Users**: Suspend ⛔ button
- **Suspended Users**: Reactivate ✓ button

### 3. Available User Statuses

- **Pending**: New users awaiting approval
- **Approved**: Active users with full access
- **Rejected**: Users whose registration was denied
- **Suspended**: Temporarily disabled accounts

## Usage

### Change Status via Dropdown

1. Navigate to **Admin Dashboard → User Management**
2. Click on a user to view their details
3. In the **Admin Actions** card, find the **Change Status** dropdown
4. Select the new status from the dropdown
5. Click **Apply** to save the change
6. Confirm the action when prompted

### Quick Actions

1. Navigate to **Admin Dashboard → User Management**
2. Find the user in the list
3. Use the action buttons in the rightmost column:
   - Green checkmark (✓) to approve or reactivate
   - Red X (✗) to reject
   - Orange ban (⛔) to suspend

## Security & Restrictions

- Administrators cannot change their own status
- Status changes are logged for audit purposes
- All actions require confirmation to prevent accidents
- Only administrators can access these features

## Status Transitions

### Valid Transitions:
- **Pending** → Approved, Rejected
- **Approved** → Suspended
- **Rejected** → Approved (via dropdown)
- **Suspended** → Approved

### Special Behaviors:
- Approving a pending user sets `approved_at` timestamp
- Rejecting a pending user sets `rejected_at` timestamp
- Status changes are immediately effective

## Implementation Details

### New Route
```python
@admin_bp.route('/users/<int:user_id>/change-status', methods=['POST'])
def change_user_status(user_id):
    # Flexible status change endpoint
```

### Template Updates
- `admin/user_detail.html`: Added status dropdown form
- `admin/users.html`: Added quick action buttons

### Security Checks
- Login required
- Admin role required
- Cannot modify own account
- CSRF protection enabled
