"""
Main Blueprint

This module handles the main application routes including
the dashboard, settings, and digest generation.
"""
from flask import Blueprint

# Create blueprint
main_bp = Blueprint('main', __name__)

# Import routes to register them with the blueprint
from app.main import routes
