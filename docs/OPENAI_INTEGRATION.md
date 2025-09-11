# OpenAI Integration Guide

This document explains how the Email Summarizer uses OpenAI for intelligent email and calendar summarization.

> **Note**: This project uses OpenAI Python SDK v1.0+ which has a new API syntax. Make sure you have `openai>=1.0.0` installed.

## Overview

The Email Summarizer can leverage OpenAI's GPT models to provide:
- Intelligent email summarization with key points extraction
- AI-powered 4D classification with reasoning
- Smart calendar insights and time management tips
- Privacy-aware content processing

## Configuration

To enable OpenAI integration, add these settings to your `.env` file:

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4 for better quality
```

## How It Works

### 1. Email Summarization

When OpenAI is configured, the system:

1. **Groups emails by conversation** using conversation IDs
2. **Applies 4D classification** (Do, Delegate, Defer, Delete) using keywords
3. **Generates AI summaries** that include:
   - Main topic and key points
   - Action items and urgency level
   - Context-aware recommendations

### 2. Calendar Analysis

For calendar events, OpenAI provides:
- Daily overview with meeting patterns
- Time management recommendations
- Meeting preparation priorities
- Focus time optimization tips

### 3. Privacy Protection

The system respects privacy settings:

- **Privacy Mode OFF** (default): Shows real names and emails for better usability
- **Privacy Mode ON**: Redacts emails, phones, SSNs, names, etc. before processing

Privacy settings are configured in user settings:
```
Settings → Privacy → Include private content [Toggle]
```

### 4. 4D Framework Classification

The AI enhances the keyword-based classification with contextual understanding:

- **DO**: "urgent", "asap", "deadline", "please complete"
- **DELEGATE**: "assign", "delegate", "forward to", "handle this"
- **DEFER**: "later", "next week", "schedule", "when possible"
- **DELETE**: Automated emails, notifications, spam

## Implementation Details

### OpenAI Service (`app/services/openai_service.py`)

The service uses OpenAI Python SDK v1.0+ and provides these main methods:

```python
from openai import OpenAI

# Initialize the client
client = OpenAI(api_key="your-api-key")

# Example API call (v1.0+ syntax)
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Service methods:
# Summarize email conversations
summaries = openai_service.summarize_emails(
    conversations,
    include_private=False  # Respects privacy settings
)

# Generate calendar insights
calendar_data = openai_service.summarize_calendar(calendar_data)

# AI-powered classification
classification = openai_service.classify_with_ai(email_content)
```

### Integration Points

1. **Digest Service** (`app/services/digest_service.py`):
   - Checks if OpenAI is configured
   - Applies AI summarization after initial processing
   - Falls back to heuristic methods if OpenAI fails

2. **Digest Generator** (`app/services/digest_generator.py`):
   - Includes AI summaries in the final digest
   - Shows AI insights in recommendation cards

## API Usage and Costs

- **Default Model**: GPT-3.5-turbo (cost-effective)
- **Premium Model**: GPT-4 (better quality, higher cost)
- **Token Limits**: 
  - Email summaries: ~150 tokens per conversation
  - Calendar insights: ~300 tokens per analysis
- **Daily Usage**: ~2,000-3,000 tokens per digest

## Fallback Behavior

If OpenAI is not configured or fails:
1. System uses keyword-based classification
2. Generates simple heuristic summaries
3. Provides basic calendar statistics
4. All core features remain functional

## Security Considerations

1. **API Key Protection**: Store in `.env`, never commit to version control
2. **Data Privacy**: Consider privacy mode for sensitive emails
3. **Rate Limiting**: Built-in retry logic and error handling
4. **Data Retention**: OpenAI doesn't retain API data (check current policies)

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Add `OPENAI_API_KEY` to your `.env` file
   - Restart the Flask application

2. **"AI summarization failed"**
   - Check API key validity
   - Verify internet connectivity
   - Check OpenAI service status

3. **Poor Summary Quality**
   - Consider upgrading to GPT-4
   - Ensure privacy mode isn't over-redacting
   - Check email content length

### Debug Mode

Enable debug logging in `.env`:
```env
LOG_LEVEL=DEBUG
```

Check logs for detailed OpenAI interactions:
```bash
tail -f logs/app.log | grep -i openai
```

## Best Practices

1. **Start with GPT-3.5-turbo** for cost-effectiveness
2. **Enable privacy mode** by default
3. **Monitor API usage** in OpenAI dashboard
4. **Set usage alerts** to control costs
5. **Test with sample data** before production use

## Future Enhancements

- Custom prompts for different industries
- Multi-language support
- Voice summaries using OpenAI TTS
- Automatic email response drafting
- Meeting agenda generation
