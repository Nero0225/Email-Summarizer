"""
Authentication Blueprint

This module handles user authentication including login, logout,
registration, and Microsoft OAuth integration.
"""
from flask import Blueprint

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Import routes to register them with the blueprint
from app.auth import routes
