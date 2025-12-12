#!/usr/bin/env python3
"""
Configuration management for Flask backend
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent
BACKEND_DIR = Path(__file__).parent

class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "portfolio.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Binance API (loaded from .env in parent directory)
    BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET')
    BINANCE_TESTNET = os.environ.get('BINANCE_TESTNET', 'false').lower() == 'true'

    # Auto-refresh settings
    AUTO_REFRESH_INTERVAL = 10  # seconds
    SNAPSHOT_INTERVAL = 60  # refreshes (60 * 10s = 10 minutes)

    # Portfolio settings
    MIN_BALANCE_USD = 5.0  # Minimum balance to display

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
