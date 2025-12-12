#!/usr/bin/env python3
"""
Portfolio utility functions
Shared functions for portfolio refresh operations
"""
import logging
from datetime import datetime
from db.models import db, PortfolioBalance

logger = logging.getLogger(__name__)


def refresh_portfolio_from_binance(trader, min_value=5.0):
    """
    Refresh portfolio from Binance and update database

    Args:
        trader: BinanceTrader instance
        min_value: Minimum USD value threshold (default: 5.0)

    Returns:
        tuple: (fresh_balances, total_value_usd)

    Raises:
        ValueError: If no balances found above threshold
    """
    # Get fresh balances
    fresh_balances = trader.get_all_balances_usd(min_value)

    if not fresh_balances:
        raise ValueError(f"No balances found above ${min_value} threshold")

    # Calculate total
    total_value_usd = sum(data['usd_value'] for data in fresh_balances.values())

    # Update database cache
    update_portfolio_balances(fresh_balances, total_value_usd)

    logger.info(f"✅ Portfolio refreshed: ${total_value_usd:.2f} ({len(fresh_balances)} assets)")

    return fresh_balances, total_value_usd


def update_portfolio_balances(fresh_balances, total_value_usd):
    """
    Update database with fresh portfolio balances from Binance

    Args:
        fresh_balances: Dict of {asset: {balance, free, locked, usd_value}}
        total_value_usd: Total portfolio value in USD

    Returns:
        int: Number of balances updated
    """
    try:
        # Delete old balances
        PortfolioBalance.query.delete()

        # Insert fresh balances
        for asset, data in fresh_balances.items():
            percentage = (data['usd_value'] / total_value_usd * 100) if total_value_usd > 0 else 0

            balance = PortfolioBalance(
                asset=asset,
                balance=data['balance'],
                free=data['free'],
                locked=data['locked'],
                usd_value=data['usd_value'],
                percentage=percentage,
                last_updated=datetime.utcnow()
            )
            db.session.add(balance)

        db.session.commit()

        logger.info(f"✅ Portfolio balances updated: {len(fresh_balances)} assets")

        return len(fresh_balances)

    except Exception as e:
        logger.error(f"Error updating portfolio balances: {e}")
        db.session.rollback()
        raise
