"""
Admin Blueprint

This module handles administrative functions including
user management, system monitoring, and configuration.
"""
from flask import Blueprint

# Create blueprint with admin prefix
admin_bp = Blueprint('admin', __name__)

# Import routes to register them with the blueprint
from app.admin import routes
