"""
Flask Application Factory
"""

from flask import Flask
from flask_cors import CORS
import logging
import os

def create_app():
    """Create and configure Flask application"""

    app = Flask(__name__)

    # Configure CORS
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Register routes
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'fabric-conversion-api'}, 200

    return app
