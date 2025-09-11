# Email Summarizer - AI-Powered Daily Digest

A professional Flask application that generates intelligent daily digests from your Microsoft 365 emails and calendar, using AI to classify and prioritize your communications.

## 🌟 Features

### Core Functionality
- **Microsoft 365 Integration**: Seamless connection with Outlook email and calendar
- **AI-Powered Classification**: Uses the 4D Framework (Do, Delegate, Defer, Delete) to categorize emails
- **Smart Calendar Analysis**: Identifies meeting patterns and calculates available focus time
- **Privacy Mode**: Optional PII redaction to protect sensitive information when needed
- **Unlimited Generation**: Generate digests as often as needed throughout the day
- **Multi-User Support**: Complete user management system with admin panel
- **Microsoft OAuth Authentication**: Secure registration and login through Microsoft 365 accounts
- **Digest Management**: Users can delete their own digests with confirmation dialogs
- **Password Management**: All users can change passwords; OAuth users get default password for dual access

### Email Processing Constraints
- **Volume Cap**: 200 emails maximum per digest generation
- **Folder Focus**: Inbox emails only (automatically excludes Junk, Clutter, and Other folders)
- **Smart Threading**: Groups emails by ConversationId for context-aware summarization

### Technical Highlights
- Modern Flask architecture with blueprints and application factory pattern
- RESTful API with comprehensive error handling
- Secure authentication with Flask-Login and OAuth2
- SQLAlchemy ORM with migration support
- Responsive web interface with clean, professional design
- Comprehensive logging and monitoring capabilities

## 📋 Prerequisites

- Python 3.8 or higher
- Microsoft Azure account (for Graph API access)
- OpenAI API key (for AI processing)
- Git

## 🔐 Authentication

The Email Summarizer uses Microsoft OAuth2 for secure authentication:

1. **Registration**: New users sign up using their Microsoft 365 accounts
2. **Auto-Admin Detection**: Users with email domains listed in `ADMIN_EMAIL_DOMAINS` are automatically granted admin privileges
3. **Role-Based Routing**: 
   - Admin users are automatically redirected to the Admin Dashboard
   - Regular users access the standard user dashboard
4. **Account Linking**: Existing users can link their Microsoft accounts for email/calendar access

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/email-summarizer.git
cd email-summarizer
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy example environment file
cp env.template .env

# Edit .env with your configuration
# Required: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, OPENAI_API_KEY
# Configure ADMIN_EMAIL_DOMAINS for automatic admin detection
```

### 4. Initialize Database
```bash
# Create database tables
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Create admin user
flask create-admin

# Or use the initialization script
python init_db.py

# For existing installations, run the OAuth migration
python migrate_to_oauth.py
```

### 5. Run the Application
```bash
# Development mode
python run.py

# Production mode with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

The application will be available at `http://localhost:5000`

## 🔧 Configuration

### Microsoft Azure Setup

1. Register an application in Azure Portal
2. Add required permissions:
   - `Mail.Read`
   - `Calendars.Read`
   - `User.Read`
3. Create a client secret
4. Add redirect URI: `http://localhost:5000/auth/callback`

### Environment Variables

Key configuration options in `.env`:

```env
# Microsoft Graph API
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=common

# OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-3.5-turbo

# Application Settings
MAX_EMAILS_PER_DIGEST=200
# DAILY_DIGEST_LIMIT=1  # Deprecated - no limit
DEFAULT_WORK_START_HOUR=9
DEFAULT_WORK_END_HOUR=17

# Admin Configuration
ADMIN_EMAIL_DOMAINS=admin.com,administrator.com  # Comma-separated list of admin email domains
```

## 📁 Project Structure

```
email-summarizer/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration classes
│   ├── models/              # Database models
│   │   ├── user.py          # User model
│   │   └── digest.py        # Digest-related models
│   ├── auth/                # Authentication blueprint
│   ├── main/                # Main application blueprint
│   ├── admin/               # Admin panel blueprint
│   ├── api/                 # REST API blueprint
│   ├── services/            # Business logic services
│   │   ├── digest_service.py
│   │   ├── microsoft_service.py
│   │   ├── email_service.py
│   │   └── ...
│   ├── utils/               # Utility functions
│   ├── static/              # CSS, JS, images
│   └── templates/           # HTML templates
├── migrations/              # Database migrations
├── tests/                   # Test suite
├── docs/                    # Documentation
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔌 API Documentation

### Authentication
All API endpoints require authentication via session cookies or API key.

### Main Endpoints

#### Generate Digest
```http
POST /api/v1/digest/generate
```
Generates a new daily digest for the authenticated user.

#### Get Digest History
```http
GET /api/v1/digest/history?page=1&per_page=10
```
Returns paginated digest history.

#### Update Settings
```http
PUT /api/v1/settings
Content-Type: application/json

{
  "working_hours_start": 9,
  "working_hours_end": 17,
  "privacy_mode": true
}
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_digest_service.py
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

### Production Checklist

- [ ] Set strong SECRET_KEY
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS with proper certificates
- [ ] Configure proper logging
- [ ] Set up monitoring (e.g., Sentry)
- [ ] Enable rate limiting
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 app/
black app/ --check

# Run type checking
mypy app/
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Microsoft Graph API for email and calendar access
- OpenAI for intelligent text processing
- Flask community for the excellent framework
- All contributors and testers

## 📞 Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information

## 🗺️ Roadmap

### Version 1.1
- [ ] Slack/Teams integration
- [ ] Multiple calendar support
- [ ] Email template responses
- [ ] Mobile app

### Version 1.2
- [ ] Advanced AI insights
- [ ] Team collaboration features
- [ ] Analytics dashboard
- [ ] Webhook support

---

Built with ❤️ by the Email Summarizer Team