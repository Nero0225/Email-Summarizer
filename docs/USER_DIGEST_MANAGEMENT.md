# User Digest Management

## Overview

Users can now manage their daily digests with full control over deletion. This feature allows users to clean up old digests or remove incorrectly generated ones.

## Features

### 1. Delete from Digest View Page

When viewing a specific digest, users will find a **Delete** button in the header:
- Location: Top-right button group (next to Dashboard, Print, and Share buttons)
- Appearance: Red outline button with trash icon
- Confirmation: Modal dialog to prevent accidental deletions

### 2. Delete from Dashboard

On the main dashboard, each digest in the "Recent Digests" list has a delete button:
- Location: Right side of each digest item
- Appearance: Small red trash icon button
- Quick access: Delete without opening the digest

### 3. Security & Permissions

- **User Isolation**: Users can only delete their own digests
- **Permission Check**: Server validates ownership before deletion
- **CSRF Protection**: All delete forms include CSRF tokens

### 4. Daily Usage Tracking

When deleting a digest generated today:
- The daily digest count is automatically decremented
- Allows users to generate a new digest if they delete today's

## Implementation Details

### Route
```python
@main_bp.route('/digest/<int:digest_id>/delete', methods=['POST'])
@login_required
def delete_digest(digest_id):
    # Validates user ownership
    # Updates daily usage count
    # Deletes digest record
```

### UI Components

#### Digest View Page
```html
<form method="POST" action="{{ url_for('main.delete_digest', digest_id=digest.id) }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <button type="submit" class="btn btn-outline-danger">
        <i class="fas fa-trash-alt"></i> Delete
    </button>
</form>
```

#### Dashboard List
```html
<button type="submit" class="btn btn-sm btn-outline-danger" title="Delete digest">
    <i class="fas fa-trash-alt"></i>
</button>
```

### User Experience

1. **Confirmation Dialog**: JavaScript confirmation prevents accidental deletions
2. **Success Feedback**: Flash message confirms successful deletion
3. **Error Handling**: Graceful error messages if deletion fails
4. **Redirect**: After deletion, users return to the dashboard

## Benefits

- **Storage Management**: Users can manage their digest history
- **Privacy Control**: Remove sensitive digests when needed
- **Mistake Correction**: Delete and regenerate if needed
- **Clean Interface**: Easy access to delete functionality

## Usage Scenarios

1. **Accidental Generation**: Delete test or accidental digests
2. **Privacy Concerns**: Remove digests before sharing device
3. **Storage Cleanup**: Remove old digests to declutter
4. **Regeneration**: Delete and create new digest with updated settings
