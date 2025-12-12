#!/usr/bin/env python3
"""
Performance API endpoints
Handles TWR analytics, P&L tracking, snapshots, and cash flows
"""
import logging
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from services.session_manager import session_manager
from core.performance_tracker import PerformanceTracker
from db.models import db, Snapshot, CashFlow

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__)


@performance_bp.route('/snapshots', methods=['GET'])
def get_snapshots():
    """
    GET /api/performance/snapshots?start_date=&end_date=
    Get snapshots for a period

    Returns:
        {snapshots: [...], count: int}
    """
    try:
        # Parse query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        query = Snapshot.query

        # Apply date filters if provided
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str)
            query = query.filter(Snapshot.timestamp >= start_date)

        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str)
            query = query.filter(Snapshot.timestamp <= end_date)

        # Order by timestamp
        snapshots = query.order_by(Snapshot.timestamp).all()

        return jsonify({
            'snapshots': [s.to_dict() for s in snapshots],
            'count': len(snapshots)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching snapshots: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/snapshots', methods=['POST'])
def create_snapshot():
    """
    POST /api/performance/snapshots
    Create a manual snapshot of current portfolio

    Returns:
        {message: str, snapshot: {...}}
    """
    try:
        trader = session_manager.get_trader()
        tracker = PerformanceTracker(trader)

        success = tracker.save_current_snapshot()

        if success:
            # Get the latest snapshot
            latest = Snapshot.query.order_by(Snapshot.timestamp.desc()).first()

            return jsonify({
                'message': 'Snapshot created successfully',
                'snapshot': latest.to_dict() if latest else None
            }), 201
        else:
            return jsonify({'error': 'Failed to create snapshot'}), 500

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/cashflows', methods=['GET'])
def get_cash_flows():
    """
    GET /api/performance/cashflows?start_date=&end_date=
    Get cash flows for a period

    Returns:
        {cashflows: [...], count: int, total_deposits: float, total_withdrawals: float}
    """
    try:
        # Parse query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        query = CashFlow.query

        # Apply date filters if provided
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str)
            query = query.filter(CashFlow.timestamp >= start_date)

        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str)
            query = query.filter(CashFlow.timestamp <= end_date)

        # Order by timestamp
        cash_flows = query.order_by(CashFlow.timestamp).all()

        # Calculate totals
        total_deposits = sum(cf.amount_usd for cf in cash_flows if cf.amount_usd > 0)
        total_withdrawals = sum(abs(cf.amount_usd) for cf in cash_flows if cf.amount_usd < 0)

        return jsonify({
            'cashflows': [cf.to_dict() for cf in cash_flows],
            'count': len(cash_flows),
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals
        }), 200

    except Exception as e:
        logger.error(f"Error fetching cash flows: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/cashflows', methods=['POST'])
def create_cash_flow():
    """
    POST /api/performance/cashflows
    Add a cash flow (deposit or withdrawal)

    Request Body:
        {amount_usd: float, type: str, description: str}

    Returns:
        {message: str, cashflow: {...}}
    """
    try:
        data = request.get_json()

        # Validate input
        if not data or 'amount_usd' not in data or 'type' not in data:
            return jsonify({'error': 'Missing required fields: amount_usd, type'}), 400

        amount_usd = float(data['amount_usd'])
        cf_type = data['type']
        description = data.get('description', '')

        # Validate type
        if cf_type not in ['DEPOSIT', 'WITHDRAW']:
            return jsonify({'error': 'Invalid type. Must be DEPOSIT or WITHDRAW'}), 400

        # For withdrawals, make amount negative
        if cf_type == 'WITHDRAW' and amount_usd > 0:
            amount_usd = -amount_usd

        # Create cash flow
        cash_flow = CashFlow(
            timestamp=datetime.utcnow(),
            amount_usd=amount_usd,
            type=cf_type,
            description=description
        )

        db.session.add(cash_flow)
        db.session.commit()

        logger.info(f"💰 Cash flow created: {cf_type} {amount_usd:+.2f}€")

        return jsonify({
            'message': 'Cash flow created successfully',
            'cashflow': cash_flow.to_dict()
        }), 201

    except ValueError:
        return jsonify({'error': 'Invalid amount_usd value'}), 400
    except Exception as e:
        logger.error(f"Error creating cash flow: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/twr/<int:days>', methods=['GET'])
def get_twr(days):
    """
    GET /api/performance/twr/:days
    Calculate TWR for a period

    Path:
        days: Number of days (7, 30, 90, etc.)

    Returns:
        {
            period_days: int,
            twr: float,
            twr_percent: float,
            twr_annualized: float,
            start_date: str,
            end_date: str
        }
    """
    try:
        trader = session_manager.get_trader()
        tracker = PerformanceTracker(trader)

        # Calculate metrics
        metrics = tracker.calculate_performance_metrics(days)

        if not metrics or metrics['twr'] is None:
            return jsonify({
                'error': f'Not enough data for {days} days period',
                'period_days': days
            }), 200  # 200 because it's not an error, just not enough data

        # Add percentage representation
        metrics['twr_percent'] = metrics['twr'] * 100 if metrics['twr'] is not None else None
        metrics['twr_annualized_percent'] = metrics['twr_annualized'] * 100 if metrics['twr_annualized'] is not None else None

        # Convert dates to ISO format
        metrics['start_date'] = metrics['start_date'].isoformat()
        metrics['end_date'] = metrics['end_date'].isoformat()

        return jsonify(metrics), 200

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error calculating TWR for {days} days: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/pnl/<int:days>', methods=['GET'])
def get_pnl(days):
    """
    GET /api/performance/pnl/:days
    Calculate simple P&L for a period

    Formula: P&L = (Current Value - Initial Value) - Net Cash Flow

    Path:
        days: Number of days (7, 30, 90, etc.) - 0 for total

    Returns:
        {
            pnl_usd: float,
            pnl_percent: float,
            invested_capital: float,
            current_value: float,
            period_days: int,
            period_start: str,
            period_end: str
        }
    """
    try:
        trader = session_manager.get_trader()
        tracker = PerformanceTracker(trader)

        # Calculate simple P&L
        if days == 0:
            pnl = tracker.calculate_simple_pnl(days=None)
        else:
            pnl = tracker.calculate_simple_pnl(days=days)

        # Format dates for JSON
        pnl['period_start'] = pnl['period_start'].isoformat()
        pnl['period_end'] = pnl['period_end'].isoformat()

        # Compatibility with old frontend format
        pnl['realized_pnl_usd'] = pnl['pnl_usd']  # All P&L is "realized" now
        pnl['unrealized_pnl_usd'] = 0  # No separate unrealized
        pnl['total_pnl_usd'] = pnl['pnl_usd']
        pnl['total_fees_usd'] = 0  # Fees included in P&L
        pnl['trade_count'] = 0  # Not tracked anymore

        return jsonify(pnl), 200

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error calculating P&L for {days} days: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    GET /api/performance/stats
    Get tracking statistics

    Returns:
        {
            tracking_days: int,
            total_snapshots: int,
            total_cashflows: int,
            total_deposits_usd: float,
            total_withdrawals_usd: float,
            first_snapshot_date: str,
            last_snapshot_date: str
        }
    """
    try:
        trader = session_manager.get_trader()
        tracker = PerformanceTracker(trader)

        # Get tracking stats
        stats = tracker.get_tracking_stats()

        # Get cash flow count and totals
        cashflow_count = CashFlow.query.count()
        all_cash_flows = CashFlow.query.all()

        total_deposits = sum(cf.amount_usd for cf in all_cash_flows if cf.amount_usd > 0)
        total_withdrawals = sum(abs(cf.amount_usd) for cf in all_cash_flows if cf.amount_usd < 0)

        # Format dates - match frontend expectations
        result = {
            'tracking_days': stats['days'],
            'total_snapshots': stats['total_snapshots'],
            'total_cashflows': cashflow_count,
            'total_deposits_usd': total_deposits,
            'total_withdrawals_usd': total_withdrawals,
            'first_snapshot_date': stats['first_snapshot'].isoformat() if stats['first_snapshot'] else None,
            'last_snapshot_date': stats['last_snapshot'].isoformat() if stats['last_snapshot'] else None
        }

        return jsonify(result), 200

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500
