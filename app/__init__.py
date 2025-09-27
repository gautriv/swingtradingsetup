"""
Flask application initialization.
"""

from flask import Flask
from config import Config

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Register blueprints/routes
    from app.routes import main
    app.register_blueprint(main)
    
    return app
