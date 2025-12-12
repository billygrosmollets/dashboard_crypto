#!/usr/bin/env python3
"""
Flask Application Factory
Main entry point for the Binance Portfolio Manager backend
"""
import logging
from flask import Flask
from flask_cors import CORS
from config import config
from db.models import db
from services.session_manager import session_manager
from utils.env_loader import load_env_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    """
    Application factory pattern

    Args:
        config_name: Configuration name ('development' or 'production')

    Returns:
        Flask app instance
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    logger.info(f"📝 Configuration loaded: {config_name}")

    # Load environment variables from .env
    load_env_file()

    # Initialize database
    db.init_app(app)

    with app.app_context():
        db.create_all()
        logger.info("✅ Database initialized")

    # Initialize Binance session
    api_key = app.config.get('BINANCE_API_KEY')
    api_secret = app.config.get('BINANCE_API_SECRET')
    testnet = app.config.get('BINANCE_TESTNET', False)

    if api_key and api_secret:
        session_manager.initialize(api_key, api_secret, testnet)
        logger.info("✅ Binance session initialized")
    else:
        logger.warning("⚠️  Binance API credentials not found in configuration")

    # Enable CORS for Vue.js frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://localhost:3000"],  # Vite default port
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    logger.info("✅ CORS configured")

    # Register API blueprints
    from api.portfolio import portfolio_bp
    from api.performance import performance_bp
    from api.rebalancing import rebalancing_bp

    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(performance_bp, url_prefix='/api/performance')
    app.register_blueprint(rebalancing_bp, url_prefix='/api/rebalancing')

    logger.info("✅ Portfolio API registered")
    logger.info("✅ Performance API registered")
    logger.info("✅ Rebalancing API registered")

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'trader_initialized': session_manager.is_initialized()
        }

    logger.info("🚀 Flask application created successfully")
    return app


if __name__ == '__main__':
    app = create_app('development')

    # Start auto-refresh service
    from services.auto_refresh import start_auto_refresh
    start_auto_refresh(app)

    logger.info("=" * 60)
    logger.info("🚀 Starting Binance Portfolio Manager Backend")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
