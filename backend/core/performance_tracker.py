#!/usr/bin/env python3
"""
Performance Tracker - TWR (Time-Weighted Return) calculations
Adapted to use SQLAlchemy models instead of JSON files
PRESERVED: Original TWR calculation logic (lines 335-421 from performance_tracker.py)
"""
import logging
from datetime import datetime, timedelta
from db.models import db, Snapshot, CashFlow

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Performance tracker with TWR calculations
    Uses SQLAlchemy models for data persistence
    """

    def __init__(self, trader):
        self.trader = trader

    def save_current_snapshot(self):
        """
        Save a snapshot of the current portfolio
        Called by auto-refresh service every 2 hours
        """
        try:
            balances = self.trader.get_all_balances_usd(1.0)
            total_value = sum(b['usd_value'] for b in balances.values())

            if total_value == 0:
                logger.warning("Portfolio vide, snapshot ignoré")
                return False

            # Compose snapshot data
            composition = {}
            for asset, data in balances.items():
                if data['usd_value'] > 1.0:  # Only significant positions
                    composition[asset] = {
                        'balance': data['balance'],
                        'usd_value': data['usd_value'],
                        'percentage': (data['usd_value'] / total_value * 100) if total_value > 0 else 0
                    }

            # Create snapshot
            snapshot = Snapshot(
                timestamp=datetime.utcnow(),
                total_value_usd=total_value
            )
            snapshot.set_composition(composition)

            db.session.add(snapshot)
            db.session.commit()

            logger.info(f"📸 Snapshot saved: ${total_value:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            db.session.rollback()
            return False

    def get_tracking_stats(self):
        """Get tracking statistics (days, snapshot count, etc.)"""
        try:
            snapshots = Snapshot.query.order_by(Snapshot.timestamp).all()

            if not snapshots:
                return {'days': 0, 'first_snapshot': None, 'total_snapshots': 0}

            first_snapshot = snapshots[0].timestamp
            last_snapshot = snapshots[-1].timestamp
            days_tracking = (last_snapshot - first_snapshot).days

            return {
                'days': days_tracking,
                'first_snapshot': first_snapshot,
                'last_snapshot': last_snapshot,
                'total_snapshots': len(snapshots)
            }

        except Exception as e:
            logger.error(f"Error getting tracking stats: {e}")
            return {'days': 0, 'first_snapshot': None, 'total_snapshots': 0}

    def calculate_twr(self, start_date, end_date):
        """
        Calculate TWR for a given period
        PRESERVED: Original logic from performance_tracker.py lines 335-394
        """
        try:
            # Get snapshots and cash flows for the period
            snapshots_query = Snapshot.query.filter(
                Snapshot.timestamp >= start_date,
                Snapshot.timestamp <= end_date
            ).order_by(Snapshot.timestamp).all()

            cash_flows_query = CashFlow.query.filter(
                CashFlow.timestamp >= start_date,
                CashFlow.timestamp <= end_date
            ).order_by(CashFlow.timestamp).all()

            # Convert to dict format (matching original interface)
            snapshots = [
                {
                    'timestamp': s.timestamp,
                    'total_value': s.total_value_usd,
                    'composition': s.get_composition()
                }
                for s in snapshots_query
            ]

            cash_flows = [
                {
                    'timestamp': cf.timestamp,
                    'amount': cf.amount_usd,
                    'type': cf.type,
                    'description': cf.description
                }
                for cf in cash_flows_query
            ]

            if len(snapshots) < 2:
                return None

            # Create periods based on cash flows
            periods = []
            period_start = snapshots[0]

            # Sort all events by timestamp
            all_events = []
            for snapshot in snapshots[1:]:
                all_events.append(('snapshot', snapshot))
            for cf in cash_flows:
                all_events.append(('cash_flow', cf))

            all_events.sort(key=lambda x: x[1]['timestamp'])

            # Create periods
            current_start = period_start
            cumulative_cf = 0

            for event_type, event_data in all_events:
                if event_type == 'cash_flow':
                    cumulative_cf += event_data['amount']
                elif event_type == 'snapshot':
                    # End of period
                    periods.append({
                        'start_value': current_start['total_value'],
                        'end_value': event_data['total_value'],
                        'cash_flow': cumulative_cf,
                        'start_time': current_start['timestamp'],
                        'end_time': event_data['timestamp']
                    })

                    # New period
                    current_start = event_data
                    cumulative_cf = 0

            # Calculate TWR
            cumulative_return = 1.0

            for period in periods:
                # Adjusted value after cash flow (at beginning of period)
                adjusted_start = period['start_value'] + period['cash_flow']

                # Skip if adjusted start is negative or zero (withdrawal of entire portfolio)
                if adjusted_start > 0:
                    # TWR formula: (End Value - Adjusted Start) / Adjusted Start
                    # = (End - (Start + CF)) / (Start + CF)
                    period_return = (period['end_value'] - adjusted_start) / adjusted_start
                    cumulative_return *= (1 + period_return)

            twr = cumulative_return - 1
            return twr

        except Exception as e:
            logger.error(f"Error calculating TWR: {e}")
            return None

    def calculate_performance_metrics(self, days):
        """
        Calculate all performance metrics for a period
        PRESERVED: Original logic from performance_tracker.py lines 397-421

        Special case: days=0 means "total" (from first to last snapshot)
        """
        try:
            # Get first and last snapshots
            first_snapshot = Snapshot.query.order_by(Snapshot.timestamp.asc()).first()
            last_snapshot = Snapshot.query.order_by(Snapshot.timestamp.desc()).first()

            if not first_snapshot or not last_snapshot:
                return None

            end_date = last_snapshot.timestamp

            # Special case: days=0 means from the beginning
            if days == 0:
                start_date = first_snapshot.timestamp
                actual_days = (end_date - start_date).days
                if actual_days == 0:
                    actual_days = 1  # Avoid division by zero
            else:
                start_date = end_date - timedelta(days=days)
                actual_days = days

            # Calculate TWR for the portfolio
            twr = self.calculate_twr(start_date, end_date)

            return {
                'period_days': actual_days,
                'twr': twr,
                'twr_annualized': ((1 + twr) ** (365 / actual_days) - 1) if twr is not None and actual_days > 0 and actual_days <= 365 else None,
                'start_date': start_date,
                'end_date': end_date,
                'start_value': first_snapshot.total_value_usd if days == 0 else None,
                'end_value': last_snapshot.total_value_usd
            }

        except Exception as e:
            logger.error(f"Error calculating metrics for {days}d: {e}")
            return None

    def calculate_simple_pnl(self, days=None):
        """
        Calculate simple P&L based on snapshots and cash flows

        Formula: P&L = (End Snapshot - Start Snapshot) - Net Deposits

        Args:
            days: Number of days to analyze (None = total since beginning)

        Returns:
            {
                'pnl_usd': float,              # Total P&L in USD
                'invested_capital': float,     # Total invested (deposits - withdrawals)
                'current_value': float,        # Current portfolio value (from last snapshot)
                'pnl_percent': float,          # P&L as percentage of invested capital
                'period_days': int,
                'period_start': datetime,
                'period_end': datetime
            }
        """
        try:
            # Get the last snapshot (current value)
            last_snapshot = Snapshot.query.order_by(Snapshot.timestamp.desc()).first()

            if not last_snapshot:
                logger.warning("No snapshots available for P&L calculation")
                return {
                    'pnl_usd': 0,
                    'invested_capital': 0,
                    'current_value': 0,
                    'initial_value': 0,
                    'pnl_percent': 0,
                    'total_deposits': 0,
                    'total_withdrawals': 0,
                    'net_cash_flow': 0,
                    'period_days': 0,
                    'period_start': datetime.utcnow(),
                    'period_end': datetime.utcnow()
                }

            current_value = last_snapshot.total_value_usd
            end_date = last_snapshot.timestamp

            if days is None or days == 0:
                # Total: from first snapshot to last snapshot
                first_snapshot = Snapshot.query.order_by(Snapshot.timestamp.asc()).first()
                start_date = first_snapshot.timestamp
                initial_value = first_snapshot.total_value_usd
                actual_days = (end_date - start_date).days
            else:
                # Period: from X days ago to last snapshot
                start_date = end_date - timedelta(days=days)

                # Find closest snapshot to start date
                start_snapshot = Snapshot.query.filter(
                    Snapshot.timestamp >= start_date
                ).order_by(Snapshot.timestamp.asc()).first()

                if start_snapshot:
                    initial_value = start_snapshot.total_value_usd
                    start_date = start_snapshot.timestamp
                else:
                    # No snapshot in period, use first available
                    first_snapshot = Snapshot.query.order_by(Snapshot.timestamp.asc()).first()
                    initial_value = first_snapshot.total_value_usd if first_snapshot else 0
                    start_date = first_snapshot.timestamp if first_snapshot else end_date

                actual_days = days

            # Get cash flows in period
            cash_flows = CashFlow.query.filter(
                CashFlow.timestamp >= start_date,
                CashFlow.timestamp <= end_date
            ).all()

            # Calculate net deposits (positive) and withdrawals (negative)
            total_deposits = sum(cf.amount_usd for cf in cash_flows if cf.amount_usd > 0)
            total_withdrawals = sum(abs(cf.amount_usd) for cf in cash_flows if cf.amount_usd < 0)
            net_cash_flow = total_deposits - total_withdrawals

            # P&L calculation
            # P&L = (Current - Initial) - Net Cash Flow
            pnl_usd = (current_value - initial_value) - net_cash_flow

            # Invested capital = Initial + Net Deposits
            invested_capital = initial_value + net_cash_flow

            # P&L percentage
            pnl_percent = (pnl_usd / invested_capital * 100) if invested_capital > 0 else 0

            logger.info(f"📊 P&L {actual_days}d: ${pnl_usd:+.2f} ({pnl_percent:+.2f}%)")

            return {
                'pnl_usd': pnl_usd,
                'invested_capital': invested_capital,
                'current_value': current_value,
                'initial_value': initial_value,
                'pnl_percent': pnl_percent,
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'net_cash_flow': net_cash_flow,
                'period_days': actual_days,
                'period_start': start_date,
                'period_end': end_date
            }

        except Exception as e:
            logger.error(f"Error calculating simple P&L: {e}")
            raise
