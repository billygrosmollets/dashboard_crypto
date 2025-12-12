#!/usr/bin/env python3
"""
Portfolio utility functions
Shared functions for portfolio refresh operations
"""
import logging
from services.portfolio_cache import portfolio_cache

logger = logging.getLogger(__name__)


def refresh_portfolio_from_binance(trader, min_value=5.0):
    """
    Refresh portfolio from Binance and update in-memory cache

    Args:
        trader: BinanceTrader instance
        min_value: Minimum USD value threshold (default: 5.0)

    Returns:
        tuple: (fresh_balances, total_value_usd)

    Raises:
        ValueError: If no balances found above threshold
    """
    # Get fresh balances from Binance
    fresh_balances = trader.get_all_balances_usd(min_value)

    if not fresh_balances:
        raise ValueError(f"No balances found above ${min_value} threshold")

    # Calculate total value
    total_value_usd = sum(data['usd_value'] for data in fresh_balances.values())

    # Update in-memory cache
    portfolio_cache.update_balances(fresh_balances, total_value_usd)

    logger.info(f"✅ Portfolio refreshed: ${total_value_usd:.2f} ({len(fresh_balances)} assets)")

    return fresh_balances, total_value_usd
