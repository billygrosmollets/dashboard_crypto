#!/usr/bin/env python3
"""
Portfolio API endpoints
Handles portfolio balance fetching and refresh operations
"""
import logging
from flask import Blueprint, jsonify, request
from services.session_manager import session_manager
from services.portfolio_cache import portfolio_cache
from utils.portfolio_utils import refresh_portfolio_from_binance

logger = logging.getLogger(__name__)

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/balances', methods=['GET'])
def get_balances():
    """
    GET /api/portfolio/balances
    Get cached portfolio balances from in-memory cache

    Returns:
        {
            total_value_usd: float,
            balances: [
                {asset, balance, free, locked, usd_value, percentage},
                ...
            ],
            last_updated: timestamp
        }
    """
    try:
        # Check if cache is empty (e.g., just started)
        if portfolio_cache.is_balances_empty():
            logger.info("Cache empty, forcing refresh...")
            trader = session_manager.get_trader()
            refresh_portfolio_from_binance(trader, 5.0)

        # Get balances from in-memory cache
        cache_data = portfolio_cache.get_balances()

        # Sort by USD value (descending)
        cache_data['balances'].sort(key=lambda x: x['usd_value'], reverse=True)
        cache_data['count'] = len(cache_data['balances'])

        return jsonify(cache_data), 200

    except Exception as e:
        logger.error(f"Error fetching balances: {e}")
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/refresh', methods=['POST'])
def refresh_portfolio():
    """
    POST /api/portfolio/refresh
    Force refresh portfolio from Binance API and update database cache

    Returns:
        {
            message: str,
            total_value_usd: float,
            balances_count: int
        }
    """
    try:
        trader = session_manager.get_trader()
        min_value = request.json.get('min_value', 5.0) if request.is_json else 5.0

        fresh_balances, total_value_usd = refresh_portfolio_from_binance(trader, min_value)

        return jsonify({
            'message': 'Portfolio refreshed successfully',
            'total_value_usd': total_value_usd,
            'balances_count': len(fresh_balances)
        }), 200

    except ValueError as e:
        return jsonify({
            'message': str(e),
            'total_value_usd': 0,
            'balances_count': 0
        }), 200
    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error refreshing portfolio: {e}")
        return jsonify({'error': str(e)}), 500
