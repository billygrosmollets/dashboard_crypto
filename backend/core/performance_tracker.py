#!/usr/bin/env python3

"""
Performance Tracker - TWR (Time-Weighted Return) calculations
Adapted to use SQLAlchemy models instead of JSON files
PRESERVED: Original TWR calculation logic
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

    @staticmethod
    def timestamp_to_datetime(timestamp_int):
        """Convertit un timestamp INTEGER (YYYYMMDDHHMM) en datetime"""
        if isinstance(timestamp_int, datetime):
            return timestamp_int
        timestamp_str = str(timestamp_int)
        return datetime.strptime(timestamp_str, '%Y%m%d%H%M')

    @staticmethod
    def datetime_to_timestamp(dt):
        """Convertit un datetime en timestamp INTEGER (YYYYMMDDHHMM)"""
        if isinstance(dt, int):
            return dt
        return int(dt.strftime('%Y%m%d%H%M'))

    def save_current_snapshot(self, balances=None):
        """
        Save a snapshot of the current portfolio
        Called by auto-refresh service every 30 minutes
        Automatically calculates and stores TWR/P&L metrics from inception

        Args:
            balances: Dict of balances from last_balance table (required)
        """
        try:
            if balances is None:
                logger.error("balances parameter is required")
                return False

            # Protection: avoid creating snapshots too close together (5 min minimum)
            last_snapshot = Snapshot.query.order_by(Snapshot.timestamp.desc()).first()
            if last_snapshot:
                last_dt = self.timestamp_to_datetime(last_snapshot.timestamp)
                time_since_last = (datetime.utcnow() - last_dt).total_seconds()
                if time_since_last < 300:  # Less than 5 minutes (300 seconds)
                    logger.debug(f"Snapshot skipped: last snapshot was {time_since_last:.0f}s ago")
                    return False

            total_value = sum(b['usd_value'] for b in balances.values())
            if total_value == 0:
                logger.warning("Portfolio vide, snapshot ignore")
                return False

            # Calculate performance metrics from inception
            twr_metrics = self.calculate_performance_metrics(days=0)  # 0 = total
            pnl_metrics = self.calculate_simple_pnl(days=None)  # None = total

            # Create snapshot with INTEGER timestamp format YYYYMMDDHHmm
            timestamp_int = int(datetime.utcnow().strftime('%Y%m%d%H%M'))

            snapshot = Snapshot(
                timestamp=timestamp_int,
                total_value_usd=int(total_value),
                twr=round(twr_metrics['twr'] * 100, 2) if (twr_metrics and twr_metrics['twr'] is not None) else None,
                pnl=int(pnl_metrics['pnl_usd']) if pnl_metrics else None,
                pnl_percent=round(pnl_metrics['pnl_percent'], 2) if pnl_metrics else None
            )

            db.session.add(snapshot)
            db.session.commit()

            logger.info(f"Snapshot saved: ${snapshot.total_value_usd} | TWR: {snapshot.twr:+.2f}% | P&L: ${snapshot.pnl:+d}")
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
                return {
                    'days': 0,
                    'first_snapshot': None,
                    'last_snapshot': None,
                    'total_snapshots': 0
                }

            # Convertir les timestamps INTEGER en datetime
            first_dt = self.timestamp_to_datetime(snapshots[0].timestamp)
            last_dt = self.timestamp_to_datetime(snapshots[-1].timestamp)
            days_tracking = (last_dt - first_dt).days

            return {
                'days': days_tracking,
                'first_snapshot': first_dt,
                'last_snapshot': last_dt,
                'total_snapshots': len(snapshots)
            }

        except Exception as e:
            logger.error(f"Error getting tracking stats: {e}")
            return {
                'days': 0,
                'first_snapshot': None,
                'last_snapshot': None,
                'total_snapshots': 0
            }

    def calculate_twr(self, start_date, end_date):
        """
        Calculate TWR for a given period
        PRESERVED: Original logic from performance_tracker.py lines 335-394
        """
        try:
            # Convertir les dates en format INTEGER pour la comparaison
            start_ts = self.datetime_to_timestamp(start_date)
            end_ts = self.datetime_to_timestamp(end_date)

            # Get snapshots and cash flows for the period
            snapshots_query = Snapshot.query.filter(
                Snapshot.timestamp >= start_ts,
                Snapshot.timestamp <= end_ts
            ).order_by(Snapshot.timestamp).all()

            cash_flows_query = CashFlow.query.filter(
                CashFlow.timestamp >= start_ts,
                CashFlow.timestamp <= end_ts
            ).order_by(CashFlow.timestamp).all()

            # Convert to dict format (matching original interface)
            snapshots = [
                {
                    'timestamp': self.timestamp_to_datetime(s.timestamp),
                    'total_value': s.total_value_usd
                }
                for s in snapshots_query
            ]

            cash_flows = [
                {
                    'timestamp': self.timestamp_to_datetime(cf.timestamp),
                    'amount': cf.amount_usd,
                    'type': cf.type
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

            # Convertir les timestamps en datetime
            end_date = self.timestamp_to_datetime(last_snapshot.timestamp)

            # Special case: days=0 means from the beginning
            if days == 0:
                start_date = self.timestamp_to_datetime(first_snapshot.timestamp)
                actual_days = (end_date - start_date).days
                if actual_days == 0:
                    actual_days = 1  # Avoid division by zero
            else:
                start_date = end_date - timedelta(days=days)
                actual_days = days

            # Calculate TWR for the portfolio
            twr = self.calculate_twr(start_date, end_date)

            # Calculate annualized TWR
            twr_annualized = ((1 + twr) ** (365 / actual_days) - 1) if twr is not None and actual_days > 0 and actual_days <= 365 else None

            # Log the result
            if twr is not None:
                period_label = 'total' if days == 0 else f'{days}d'
                twr_percent = twr * 100
                logger.info(f"📊 TWR {period_label}: {twr_percent:+.2f}%")

            return {
                'period_days': actual_days,
                'twr': twr,
                'twr_annualized': twr_annualized,
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
                'pnl_usd': float,           # Total P&L in USD
                'invested_capital': float,  # Total invested (deposits - withdrawals)
                'current_value': float,     # Current portfolio value (from last snapshot)
                'pnl_percent': float,       # P&L as percentage of invested capital
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
            end_date = self.timestamp_to_datetime(last_snapshot.timestamp)

            if days is None or days == 0:
                # Total: from first snapshot to last snapshot
                first_snapshot = Snapshot.query.order_by(Snapshot.timestamp.asc()).first()
                start_date = self.timestamp_to_datetime(first_snapshot.timestamp)
                initial_value = first_snapshot.total_value_usd
                actual_days = (end_date - start_date).days
            else:
                # Period: from X days ago to last snapshot
                start_date = end_date - timedelta(days=days)

                # Convertir en INTEGER pour la requête SQL
                start_ts = self.datetime_to_timestamp(start_date)

                # Find closest snapshot to start date
                start_snapshot = Snapshot.query.filter(
                    Snapshot.timestamp >= start_ts
                ).order_by(Snapshot.timestamp.asc()).first()

                if start_snapshot:
                    initial_value = start_snapshot.total_value_usd
                    start_date = self.timestamp_to_datetime(start_snapshot.timestamp)
                else:
                    # No snapshot in period, use first available
                    first_snapshot = Snapshot.query.order_by(Snapshot.timestamp.asc()).first()
                    initial_value = first_snapshot.total_value_usd if first_snapshot else 0
                    start_date = self.timestamp_to_datetime(first_snapshot.timestamp) if first_snapshot else end_date

                actual_days = days

            # Convertir les dates en INTEGER pour les requêtes SQL
            start_ts = self.datetime_to_timestamp(start_date)
            end_ts = self.datetime_to_timestamp(end_date)

            # Get cash flows in period
            cash_flows = CashFlow.query.filter(
                CashFlow.timestamp >= start_ts,
                CashFlow.timestamp <= end_ts
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

            # Log the result
            period_label = 'total' if (days is None or days == 0) else f'{days}d'
            logger.info(f"📊 P&L {period_label}: ${pnl_usd:+.2f}")

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