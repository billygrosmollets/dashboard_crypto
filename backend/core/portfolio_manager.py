#!/usr/bin/env python3
"""
Portfolio Manager - Per-asset rebalancing logic
Handles portfolio rebalancing with trade history tracking
"""
import logging
from datetime import datetime
from db.models import db, ConversionHistory

logger = logging.getLogger(__name__)

# Stablecoins list
STABLECOINS = {'USDT', 'USDC', 'BUSD', 'FDUSD', 'DAI', 'TUSD'}


class PortfolioManager:
    """
    Manages portfolio rebalancing with cost basis tracking for P&L
    """

    def __init__(self, trader):
        self.trader = trader

    def calculate_rebalancing_plan_per_asset(self, target_allocations):
        """
        Calculate rebalancing plan based on per-asset target allocations

        Args:
            target_allocations: dict {asset: target_percent}

        Returns:
            {
                'actions': [{asset, action, usd_amount, priority}],
                'current_allocation': {asset: percent},
                'target_allocation': {asset: percent},
                'total_value_usd': float
            }
        """
        try:
            # Get current balances
            balances = self.trader.get_all_balances_usd(1.0)
            total_value = sum(b['usd_value'] for b in balances.values())

            if total_value == 0:
                raise ValueError("Portfolio is empty")

            # Calculate current allocation percentages
            current_allocation = {}
            for asset, data in balances.items():
                percent = (data['usd_value'] / total_value * 100)
                if percent >= 1.0:  # Only show significant assets
                    current_allocation[asset] = round(percent, 2)

            # Minimum threshold to avoid micro-trades
            MIN_TRADE_USD = total_value * 0.005  # 0.5% of portfolio

            actions = []

            # Calculate differences for each asset in target allocation
            for asset, target_percent in target_allocations.items():
                current_percent = current_allocation.get(asset, 0)
                diff_percent = target_percent - current_percent
                diff_usd = (diff_percent / 100) * total_value

                # Only create action if difference is significant
                if abs(diff_usd) > MIN_TRADE_USD:
                    actions.append({
                        'asset': asset,
                        'action': 'ACHETER' if diff_usd > 0 else 'VENDRE',
                        'usd_amount': abs(diff_usd),
                        'priority': 1  # All have same priority now
                    })

            # Sort by USD amount descending
            actions.sort(key=lambda x: -x['usd_amount'])

            return {
                'actions': actions,
                'current_allocation': current_allocation,
                'target_allocation': target_allocations,
                'total_value_usd': total_value
            }

        except Exception as e:
            logger.error(f"Error calculating rebalancing plan: {e}")
            raise

    def get_primary_stablecoin(self):
        """
        Detect the primary stablecoin in portfolio (the one with highest balance)

        Returns:
            str: Stablecoin symbol (USDC, USDT, BUSD, etc.)
        """
        balances = self.trader.get_all_balances_usd(1.0)

        # Find stablecoins in portfolio
        stables_in_portfolio = {}
        for asset, data in balances.items():
            if asset in STABLECOINS:
                stables_in_portfolio[asset] = data['usd_value']

        if not stables_in_portfolio:
            # Default to USDT if no stablecoins found
            logger.warning("No stablecoins found in portfolio, defaulting to USDT")
            return 'USDT'

        # Return the one with highest value
        primary = max(stables_in_portfolio.items(), key=lambda x: x[1])[0]
        logger.info(f"Primary stablecoin detected: {primary}")
        return primary

    def _save_conversion_history(self, from_asset, to_asset, amount, result):
        """
        Save conversion to database for P&L tracking

        Args:
            from_asset: Asset being sold
            to_asset: Asset being bought
            amount: Quantity of from_asset
            result: Conversion result from trader.convert_asset()
        """
        try:
            conversion_type = result.get('type', 'direct')

            # Calculate result amount based on conversion type
            if conversion_type == 'direct':
                order = result.get('order', {})
                result_amount = sum(float(fill['qty']) for fill in order.get('fills', []))
            elif conversion_type == 'triangular':
                order2 = result.get('order2', {})
                result_amount = sum(float(fill['qty']) for fill in order2.get('fills', []))
            else:
                result_amount = 0

            conversion = ConversionHistory(
                timestamp=datetime.utcnow(),
                from_asset=from_asset,
                to_asset=to_asset,
                amount=amount,
                result_amount=result_amount,
                fee_usd=result.get('total_fee_usdt', 0),
                conversion_type=conversion_type,
                status='SUCCESS'
            )

            db.session.add(conversion)
            db.session.commit()

            logger.info(f"💾 Saved conversion: {amount:.8f} {from_asset} → {result_amount:.8f} {to_asset}")

        except Exception as e:
            logger.error(f"Error saving conversion history: {e}")
            db.session.rollback()

    def execute_rebalancing(self, actions):
        """
        Execute rebalancing actions

        Args:
            actions: List of actions [{asset, action, usd_amount}]

        Returns:
            List of results [{asset, action, success, message, order, fees_usd}]
        """
        results = []

        # Detect primary stablecoin to use for conversions
        primary_stable = self.get_primary_stablecoin()
        logger.info(f"💵 Using {primary_stable} as reference stablecoin for conversions")

        for action in actions:
            asset = action['asset']
            trade_action = action['action']
            usd_amount = action['usd_amount']

            try:
                # Skip if trying to convert stablecoin to itself
                if asset == primary_stable:
                    logger.info(f"⏭️  Skipping {asset} rebalancing (is the primary stablecoin)")
                    results.append({
                        'asset': asset,
                        'action': trade_action,
                        'success': True,
                        'message': f'Skipped: {asset} is the primary stablecoin, no conversion needed',
                        'fees_usd': 0
                    })
                    continue

                logger.info(f"🔄 Executing: {trade_action} {usd_amount:.2f} USD of {asset}")

                # For sells, convert USD amount to asset quantity
                if trade_action == 'VENDRE':
                    balances = self.trader.get_all_balances_usd(1.0)
                    if asset not in balances:
                        results.append({
                            'asset': asset,
                            'action': trade_action,
                            'success': False,
                            'message': f'Asset {asset} not found in portfolio',
                            'fees_usd': 0
                        })
                        continue

                    # Get current price
                    current_price = balances[asset]['usd_value'] / balances[asset]['balance'] if balances[asset]['balance'] > 0 else 0

                    if current_price == 0:
                        results.append({
                            'asset': asset,
                            'action': trade_action,
                            'success': False,
                            'message': f'Cannot determine price for {asset}',
                            'fees_usd': 0
                        })
                        continue

                    # Calculate quantity to sell
                    quantity = usd_amount / current_price

                    # Execute sell to primary stablecoin
                    result = self.trader.convert_asset(asset, primary_stable, quantity)

                    if result is None:
                        results.append({
                            'asset': asset,
                            'action': trade_action,
                            'success': False,
                            'message': f'Conversion failed: {asset} to {primary_stable}',
                            'fees_usd': 0
                        })
                        continue

                    # Save conversion history
                    self._save_conversion_history(asset, primary_stable, quantity, result)

                    results.append({
                        'asset': asset,
                        'action': trade_action,
                        'success': True,
                        'message': f'Sold {quantity:.8f} {asset} for ~{usd_amount:.2f} {primary_stable}',
                        'order': result.get('order'),
                        'fees_usd': result.get('total_fee_usdt', 0)
                    })

                else:  # ACHETER
                    # Buy with primary stablecoin
                    result = self.trader.convert_asset(primary_stable, asset, usd_amount)

                    if result is None:
                        results.append({
                            'asset': asset,
                            'action': trade_action,
                            'success': False,
                            'message': f'Conversion failed: {primary_stable} to {asset}',
                            'fees_usd': 0
                        })
                        continue

                    # Save conversion history
                    self._save_conversion_history(primary_stable, asset, usd_amount, result)

                    results.append({
                        'asset': asset,
                        'action': trade_action,
                        'success': True,
                        'message': f'Bought {asset} with ~{usd_amount:.2f} {primary_stable}',
                        'order': result.get('order'),
                        'fees_usd': result.get('total_fee_usdt', 0)
                    })

                logger.info(f"✅ Success: {trade_action} {asset}")

            except Exception as e:
                logger.error(f"❌ Error executing {trade_action} {asset}: {e}")
                results.append({
                    'asset': asset,
                    'action': trade_action,
                    'success': False,
                    'message': str(e),
                    'fees_usd': 0
                })

        return results
