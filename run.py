#!/usr/bin/env python3
"""
Email Summarizer Application Entry Point

This module serves as the entry point for running the Flask application.
It can be run directly or through a WSGI server like Gunicorn.
"""
import os
import sys
from app import create_app, db
from app.models import User

# Get environment (default to development)
env = os.environ.get('FLASK_ENV', 'development')

# Create application instance
app = create_app(env)


@app.shell_context_processor
def make_shell_context():
    """Add useful items to Flask shell context"""
    return {
        'db': db,
        'User': User
    }


if __name__ == '__main__':
    # Configuration based on environment
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║             Email Summarizer - Daily Digest              ║
    ╚══════════════════════════════════════════════════════════╝
    
    Environment: {env}
    Host: {host}
    Port: {port}
    Debug: {app.debug}
    
    Features:
    ✓ Microsoft 365 Integration
    ✓ 4D Email Classification (Do, Delegate, Defer, Delete)
    ✓ Calendar Analysis with Focus Time
    ✓ Privacy Mode with PII Redaction
    ✓ Once-per-day Digest Generation
    ✓ Multi-user Support with Admin Panel
    
    URLs:
    - Application: http://{host}:{port}/
    - Admin Panel: http://{host}:{port}/admin
    - API Docs: http://{host}:{port}/api/v1/docs
    
    Default Admin:
    - Username: admin
    - Password: {os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin123')}
    
    Press CTRL+C to quit
    """)
    
    # Try different ports if default is in use
    if env == 'development':
        ports_to_try = [port, 5001, 5002, 8000, 8080]
        
        for p in ports_to_try:
            try:
                print(f"\n→ Starting server on port {p}...")
                app.run(
                    host=host,
                    port=p,
                    debug=True,
                    use_reloader=True,
                    threaded=True
                )
                break
            except OSError as e:
                if p == ports_to_try[-1]:
                    print(f"\n✗ All ports exhausted. Error: {e}")
                    print("  Try: sudo lsof -i :5000 (to find process using port)")
                    print("  Or: export FLASK_PORT=9000 (to use different port)")
                    sys.exit(1)
                else:
                    print(f"✗ Port {p} is in use, trying next...")
    else:
        # Production mode - use single port
        app.run(
            host=host,
            port=port,
            debug=False
        )
