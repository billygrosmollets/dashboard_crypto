#!/usr/bin/env python3
"""
Session Manager - Singleton for Binance Client
Manages a single instance of BinanceTrader across the application
"""
import logging
from core.binance_trader import BinanceTrader

logger = logging.getLogger(__name__)


class SessionManager:
    """Singleton manager for BinanceTrader instance"""

    _instance = None
    _trader = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def initialize(self, api_key, api_secret, testnet=False):
        """Initialize BinanceTrader with API credentials"""
        if self._trader is None:
            try:
                self._trader = BinanceTrader(api_key, api_secret, testnet)
                logger.info("✅ BinanceTrader initialized successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to initialize BinanceTrader: {e}")
                return False
        return True

    def get_trader(self):
        """Get the BinanceTrader instance"""
        if self._trader is None:
            raise RuntimeError("SessionManager not initialized. Call initialize() first.")
        return self._trader

    def is_initialized(self):
        """Check if trader is initialized"""
        return self._trader is not None


# Global session manager instance
session_manager = SessionManager()
