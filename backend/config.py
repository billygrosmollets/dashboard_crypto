#!/usr/bin/env python3
"""
Configuration management for Flask backend
"""
import os
from pathlib import Path

# Base directory - use absolute path to avoid issues with Flask reloader
BASE_DIR = Path(__file__).parent.parent.resolve()
BACKEND_DIR = Path(__file__).parent.resolve()

class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database (can be overridden by environment variable)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Binance API (loaded from .env in parent directory)
    BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET')
    BINANCE_TESTNET = os.environ.get('BINANCE_TESTNET', 'false').lower() == 'true'

    # Auto-refresh settings
    BALANCE_UPDATE_INTERVAL = 30  # seconds - how often to update balances from Binance
    SNAPSHOT_INTERVAL = 3600  # seconds - how often to create snapshots (3600s = 1 hour)

    # Portfolio settings
    MIN_BALANCE_USD = 5.0  # Minimum balance to display

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = False  # Disabled to avoid Flask reloader issues with SQLite
    # Development database in backend folder
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{(BACKEND_DIR / "portfolio.db").as_posix()}'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Production database in data folder
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{(BASE_DIR / "data" / "portfolio.db").as_posix()}'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
