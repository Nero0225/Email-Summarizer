"""
API Blueprint

This module provides RESTful API endpoints for the Email Summarizer application.
All API routes are prefixed with /api/v1/
"""
from flask import Blueprint

# Create blueprint with API prefix
api_bp = Blueprint('api', __name__)

# Import API modules to register routes
from app.api import digest, settings, errors
