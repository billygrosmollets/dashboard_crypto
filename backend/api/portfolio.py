#!/usr/bin/env python3
"""
Portfolio API endpoints
Handles portfolio balance fetching from database
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from db.models import LastBalance

logger = logging.getLogger(__name__)

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/balances', methods=['GET'])
def get_balances():
    """
    GET /api/portfolio/balances
    Get portfolio balances from last_balance table

    Returns:
        {
            total_value_usd: float,
            balances: [
                {asset, balance, usd_value, percentage},
                ...
            ],
            timestamp: timestamp,
            count: int
        }
    """
    try:
        # Get balances from last_balance table
        last_balances = LastBalance.query.order_by(LastBalance.usd_value.desc()).all()

        if not last_balances:
            return jsonify({
                'total_value_usd': 0,
                'balances': [],
                'last_updated': None,
                'count': 0
            }), 200

        # Calculate total
        total_value_usd = sum(lb.usd_value for lb in last_balances)

        # Format response
        balances = [
            {
                'asset': lb.asset,
                'balance': lb.balance,
                'usd_value': lb.usd_value,
                'percentage': lb.percentage
            }
            for lb in last_balances
        ]

        # Use the most recent timestamp (INTEGER format YYYYMMDDHHmm)
        timestamp_int = max(lb.timestamp for lb in last_balances)

        # Convert to ISO format
        timestamp_str = str(timestamp_int)
        dt = datetime(
            year=int(timestamp_str[0:4]),
            month=int(timestamp_str[4:6]),
            day=int(timestamp_str[6:8]),
            hour=int(timestamp_str[8:10]),
            minute=int(timestamp_str[10:12])
        )

        return jsonify({
            'total_value_usd': total_value_usd,
            'balances': balances,
            'timestamp': dt.isoformat(),
            'count': len(balances)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching balances: {e}")
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/refresh', methods=['POST'])
def refresh_portfolio():
    """
    POST /api/portfolio/refresh
    Get fresh balances from last_balance table
    (Actual refresh happens in background via auto_refresh service)

    Returns:
        {
            message: str,
            total_value_usd: float,
            balances_count: int
        }
    """
    try:
        # Simply read from last_balance table
        last_balances = LastBalance.query.all()

        if not last_balances:
            return jsonify({
                'message': 'No balances available',
                'total_value_usd': 0,
                'balances_count': 0
            }), 200

        total_value_usd = sum(lb.usd_value for lb in last_balances)

        return jsonify({
            'message': 'Balances retrieved from database',
            'total_value_usd': total_value_usd,
            'balances_count': len(last_balances)
        }), 200

    except Exception as e:
        logger.error(f"Error refreshing portfolio: {e}")
        return jsonify({'error': str(e)}), 500
