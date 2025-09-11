# Email Summarization Constraints

## Overview

The Email Summarizer implements specific constraints to ensure optimal performance and focused results when fetching and processing emails from Microsoft 365.

## Implementation Details

### 1. Email Volume Cap: 200 Emails Per Run

- **Configuration**: `MAX_EMAILS_PER_DIGEST = 200` (in `app/config.py`)
- **Implementation**: Microsoft Graph API `$top` parameter limits results
- **Rationale**: Prevents overwhelming the system and ensures timely digest generation
- **Customization**: Can be modified via `MAX_EMAILS_PER_DIGEST` environment variable

### 2. Folder Inclusions: Inbox Only

- **Included**: Only emails from the Inbox folder
- **Excluded**: 
  - Junk/Spam folders
  - Clutter folder
  - Other/Archive folders
  - Sent items
  - Drafts
  - Deleted items
- **Implementation**: Graph API filter uses `parentFolderId eq 'inbox'`
- **Benefit**: Focuses on actionable emails, excluding noise

### 3. Email Threading: ConversationId Grouping

- **Grouping**: Emails are grouped by Microsoft's `conversationId`
- **Implementation**: `EmailService._group_by_conversation()` method
- **Benefits**:
  - Maintains email context
  - Reduces duplicate processing
  - Better AI summarization with full conversation context
- **Fallback**: If no conversationId exists, email ID is used

## Code Locations

### Microsoft Service (Email Fetching)
```python
# app/services/microsoft_service.py
params = {
    '$filter': f"receivedDateTime ge {start_date_str} and parentFolderId eq 'inbox'",
    '$select': 'id,subject,from,receivedDateTime,bodyPreview,conversationId,...',
    '$orderby': 'receivedDateTime desc',
    '$top': current_app.config.get('MAX_EMAILS_PER_DIGEST', 200)
}
```

### Email Service (Conversation Grouping)
```python
# app/services/email_service.py
def _group_by_conversation(self, emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    conversations = defaultdict(list)
    for email in emails:
        conv_id = email.get('conversationId')
        if conv_id:
            conversations[conv_id].append(email)
```

### Configuration
```python
# app/config.py
MAX_EMAILS_PER_DIGEST = int(os.getenv('MAX_EMAILS_PER_DIGEST', 200))
```

## API Response Structure

When emails are fetched, they include:
- `id`: Unique email identifier
- `conversationId`: Thread identifier for grouping
- `subject`: Email subject line
- `from`: Sender information
- `receivedDateTime`: Timestamp
- `bodyPreview`: Text preview
- `body`: Full email content
- `isRead`: Read status
- `importance`: Priority level
- `hasAttachments`: Attachment indicator

## Performance Considerations

1. **200 Email Limit**: Balances comprehensiveness with processing time
2. **Inbox Focus**: Reduces API calls and processing overhead
3. **Conversation Threading**: Minimizes redundant AI processing

## Monitoring

The system logs:
- Number of emails fetched
- Number of conversations created
- Processing time for email grouping

Example log entries:
```
Fetched 150 emails from Microsoft Graph API
Grouped into 45 conversations
Email processing completed in 2.3 seconds
```

## Future Enhancements

Potential improvements while maintaining constraints:
1. Configurable folder selection (while excluding Junk/Clutter)
2. Dynamic email cap based on processing capacity
3. Smart conversation threading with AI-enhanced grouping
