#!/usr/bin/env python3
"""
Portfolio API endpoints
Handles portfolio balance fetching and refresh operations
"""
import logging
from flask import Blueprint, jsonify, request
from services.session_manager import session_manager
from db.models import db, PortfolioBalance
from datetime import datetime

logger = logging.getLogger(__name__)

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/balances', methods=['GET'])
def get_balances():
    """
    GET /api/portfolio/balances
    Get cached portfolio balances from database

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
        # Get all balances from database (cache)
        balances = PortfolioBalance.query.all()

        if not balances:
            # No cached balances, trigger a refresh
            logger.info("No cached balances found, triggering refresh...")
            return refresh_portfolio()

        # Calculate total
        total_value_usd = sum(b.usd_value for b in balances)

        # Convert to dict and sort by USD value (descending)
        balances_list = [b.to_dict() for b in balances]
        balances_list.sort(key=lambda x: x['usd_value'], reverse=True)

        # Get last update timestamp
        last_updated = max(b.last_updated for b in balances) if balances else datetime.utcnow()

        return jsonify({
            'total_value_usd': total_value_usd,
            'balances': balances_list,
            'last_updated': last_updated.isoformat(),
            'count': len(balances_list)
        }), 200

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
        # Get trader instance
        trader = session_manager.get_trader()

        # Get fresh balances from Binance
        min_value = request.json.get('min_value', 5.0) if request.is_json else 5.0
        fresh_balances = trader.get_all_balances_usd(min_value)

        if not fresh_balances:
            return jsonify({
                'message': 'No balances found above minimum threshold',
                'total_value_usd': 0,
                'balances_count': 0
            }), 200

        # Calculate total and percentages
        total_value_usd = sum(data['usd_value'] for data in fresh_balances.values())

        # Update database cache
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

        logger.info(f"✅ Portfolio refreshed: ${total_value_usd:.2f} ({len(fresh_balances)} assets)")

        return jsonify({
            'message': 'Portfolio refreshed successfully',
            'total_value_usd': total_value_usd,
            'balances_count': len(fresh_balances)
        }), 200

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error refreshing portfolio: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/assets/tradeable', methods=['GET'])
def get_tradeable_assets():
    """
    GET /api/portfolio/assets/tradeable
    Get list of all tradeable assets on Binance

    Returns:
        {
            assets: [str, ...],
            count: int
        }
    """
    try:
        trader = session_manager.get_trader()
        assets = trader.get_all_tradeable_assets()

        return jsonify({
            'assets': assets,
            'count': len(assets)
        }), 200

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error fetching tradeable assets: {e}")
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/connection/test', methods=['GET'])
def test_connection():
    """
    GET /api/portfolio/connection/test
    Test Binance API connection

    Returns:
        {
            connected: bool,
            message: str
        }
    """
    try:
        trader = session_manager.get_trader()
        connected = trader.test_connection()

        return jsonify({
            'connected': connected,
            'message': 'Connected to Binance API' if connected else 'Failed to connect to Binance API'
        }), 200 if connected else 503

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({
            'connected': False,
            'message': 'Binance session not initialized'
        }), 500
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({
            'connected': False,
            'message': str(e)
        }), 500
