#!/usr/bin/env python3
"""
Unified in-memory cache for portfolio data and performance metrics
Provides thread-safe caching for balances and TWR calculations
"""
import logging
from threading import Lock
from datetime import datetime

logger = logging.getLogger(__name__)


class PortfolioCache:
    """
    Unified in-memory cache for portfolio data

    This cache stores:
    - Current portfolio balances (refreshed every 10s by auto-refresh)
    - TWR calculation results (updated automatically when new snapshot created)
    - P&L calculation results (updated automatically when new snapshot created)
    """

    def __init__(self):
        # Portfolio balances cache
        self._balances = {}
        self._total_value_usd = 0.0
        self._balances_last_updated = None

        # TWR metrics cache
        self._twr_cache = {}  # {period: metrics_dict}

        # PnL metrics cache
        self._pnl_cache = {}  # {period: pnl_dict}

        # Thread safety
        self._lock = Lock()

    # ========== Portfolio Balances Methods ==========

    def update_balances(self, balances_dict, total_value_usd):
        """
        Update portfolio balances cache (called by auto-refresh every 10s)

        Args:
            balances_dict: Dict of {asset: {balance, free, locked, usd_value}}
            total_value_usd: Total portfolio value
        """
        with self._lock:
            self._balances = balances_dict
            self._total_value_usd = total_value_usd
            self._balances_last_updated = datetime.utcnow()
            logger.debug(f"📦 Balances cache updated: ${total_value_usd:.2f} ({len(balances_dict)} assets)")

    def get_balances(self):
        """
        Get cached portfolio balances

        Returns:
            dict: {balances: list, total_value_usd: float, last_updated: str}
        """
        with self._lock:
            # Convert dict to list for API response
            balances_list = []
            for asset, data in self._balances.items():
                percentage = (data['usd_value'] / self._total_value_usd * 100) if self._total_value_usd > 0 else 0
                balances_list.append({
                    'asset': asset,
                    'balance': data['balance'],
                    'free': data['free'],
                    'locked': data['locked'],
                    'usd_value': data['usd_value'],
                    'percentage': percentage,
                    'last_updated': self._balances_last_updated.isoformat() if self._balances_last_updated else None
                })

            return {
                'balances': balances_list,
                'total_value_usd': self._total_value_usd,
                'last_updated': self._balances_last_updated.isoformat() if self._balances_last_updated else None
            }

    def is_balances_empty(self):
        """Check if balances cache is empty (e.g., after restart)"""
        with self._lock:
            return len(self._balances) == 0

    # ========== TWR Cache Methods ==========

    def get_twr(self, period):
        """
        Get cached TWR metrics for a period

        Args:
            period: Period key (e.g., '7d', '30d', 'total')

        Returns:
            dict or None: Cached TWR metrics if available, None otherwise
        """
        with self._lock:
            cached_value = self._twr_cache.get(period)
            if cached_value:
                logger.debug(f"📦 TWR cache hit for {period}")
            return cached_value

    def set_twr(self, period, metrics):
        """
        Cache TWR metrics for a period

        Args:
            period: Period key (e.g., '7d', '30d', 'total')
            metrics: TWR metrics dict
        """
        with self._lock:
            self._twr_cache[period] = metrics
            logger.debug(f"💾 TWR cached for {period}")

    # ========== PnL Cache Methods ==========

    def get_pnl(self, period):
        """
        Get cached P&L metrics for a period

        Args:
            period: Period key (e.g., '7d', '30d', 'total')

        Returns:
            dict or None: Cached P&L metrics if available, None otherwise
        """
        with self._lock:
            cached_value = self._pnl_cache.get(period)
            if cached_value:
                logger.debug(f"📦 P&L cache hit for {period}")
            return cached_value

    def set_pnl(self, period, metrics):
        """
        Cache P&L metrics for a period

        Args:
            period: Period key (e.g., '7d', '30d', 'total')
            metrics: P&L metrics dict
        """
        with self._lock:
            self._pnl_cache[period] = metrics
            logger.debug(f"💾 P&L cached for {period}")

    # ========== Utility Methods ==========

    def clear_all(self):
        """Clear all caches (useful for testing or reset)"""
        with self._lock:
            self._balances = {}
            self._total_value_usd = 0.0
            self._balances_last_updated = None
            self._twr_cache = {}
            self._pnl_cache = {}
            logger.info("🗑️ All caches cleared")


# Global cache instance
portfolio_cache = PortfolioCache()
