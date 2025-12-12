#!/usr/bin/env python3
"""
Rebalancing API endpoints
Handles category-based allocation (%BTC, %Altcoins, %Stablecoins)
"""
import logging
from flask import Blueprint, jsonify, request
from services.session_manager import session_manager
from core.portfolio_manager import PortfolioManager
from db.models import db, AllocationSettings

logger = logging.getLogger(__name__)

rebalancing_bp = Blueprint('rebalancing', __name__)

# Stablecoins list
STABLECOINS = {'USDT', 'USDC', 'BUSD', 'FDUSD', 'DAI', 'TUSD'}


@rebalancing_bp.route('/allocation', methods=['GET'])
def get_allocation():
    """
    GET /api/rebalancing/allocation
    Get current allocation settings

    Returns:
        {allocations: {asset: percent}, significant_assets: [assets >= 1%]}
    """
    try:
        # Get current balances to identify significant assets (>= 1%)
        trader = session_manager.get_trader()
        balances = trader.get_all_balances_usd(1.0)
        total_value = sum(b['usd_value'] for b in balances.values())

        significant_assets = []
        current_percentages = {}

        for asset, data in balances.items():
            percent = (data['usd_value'] / total_value * 100) if total_value > 0 else 0
            if percent >= 1.0:
                significant_assets.append(asset)
                current_percentages[asset] = round(percent, 2)

        # Get or create allocation settings
        allocation = AllocationSettings.query.first()

        if not allocation:
            # Create default allocation with current percentages
            allocation = AllocationSettings()
            allocation.set_allocations(current_percentages)
            db.session.add(allocation)
            db.session.commit()

        return jsonify({
            'allocations': allocation.get_allocations(),
            'significant_assets': significant_assets,
            'current_percentages': current_percentages,
            'total_value_usd': total_value
        }), 200

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error fetching allocation: {e}")
        return jsonify({'error': str(e)}), 500


@rebalancing_bp.route('/allocation', methods=['POST'])
def update_allocation():
    """
    POST /api/rebalancing/allocation
    Update allocation settings

    Request Body:
        {allocations: {asset: percent}}

    Returns:
        {message: str, allocation: {...}}
    """
    try:
        data = request.get_json()

        if not data or 'allocations' not in data:
            return jsonify({'error': 'Missing allocations in request body'}), 400

        allocations = data['allocations']

        # Validate percentages
        total = sum(float(percent) for percent in allocations.values())
        if abs(total - 100.0) > 0.01:  # Allow 0.01% tolerance
            return jsonify({'error': f'Percentages must sum to 100% (got {total:.2f}%)'}), 400

        # Validate all percentages are non-negative
        for asset, percent in allocations.items():
            if float(percent) < 0:
                return jsonify({'error': f'Percentage for {asset} cannot be negative'}), 400

        # Get or create allocation
        allocation = AllocationSettings.query.first()
        if not allocation:
            allocation = AllocationSettings()
            db.session.add(allocation)

        # Update values
        allocation.set_allocations(allocations)

        db.session.commit()

        logger.info(f"✅ Allocation updated: {allocations}")

        return jsonify({
            'message': 'Allocation updated successfully',
            'allocation': allocation.to_dict()
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid percentage values: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error updating allocation: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rebalancing_bp.route('/plan', methods=['POST'])
def calculate_plan():
    """
    POST /api/rebalancing/plan
    Calculate rebalancing plan based on current allocation settings

    Returns:
        {
            actions: [{asset, action, usd_amount, priority}],
            current_allocation: {asset: percent},
            target_allocation: {asset: percent},
            total_value_usd: float
        }
    """
    try:
        trader = session_manager.get_trader()
        manager = PortfolioManager(trader)

        # Get allocation settings
        allocation = AllocationSettings.query.first()
        if not allocation:
            return jsonify({'error': 'No allocation settings found. Please set allocation first.'}), 400

        # Calculate plan
        plan = manager.calculate_rebalancing_plan_per_asset(
            allocation.get_allocations()
        )

        return jsonify(plan), 200

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error calculating rebalancing plan: {e}")
        return jsonify({'error': str(e)}), 500


@rebalancing_bp.route('/execute', methods=['POST'])
def execute_rebalancing():
    """
    POST /api/rebalancing/execute
    Execute rebalancing plan

    Request Body:
        {actions: [{asset, action, usd_amount}]}

    Returns:
        {
            message: str,
            results: [{asset, action, success, message, order}],
            total_fees_usd: float
        }
    """
    try:
        data = request.get_json()

        if not data or 'actions' not in data:
            return jsonify({'error': 'Missing actions in request body'}), 400

        trader = session_manager.get_trader()
        manager = PortfolioManager(trader)

        # Execute rebalancing
        results = manager.execute_rebalancing(data['actions'])

        # Calculate total fees
        total_fees = sum(r.get('fees_usd', 0) for r in results if r.get('success'))

        logger.info(f"✅ Rebalancing executed: {len([r for r in results if r.get('success')])} success, {len([r for r in results if not r.get('success')])} failed")

        return jsonify({
            'message': 'Rebalancing execution completed',
            'results': results,
            'total_fees_usd': total_fees
        }), 200

    except RuntimeError as e:
        logger.error(f"Session not initialized: {e}")
        return jsonify({'error': 'Binance session not initialized'}), 500
    except Exception as e:
        logger.error(f"Error executing rebalancing: {e}")
        return jsonify({'error': str(e)}), 500


