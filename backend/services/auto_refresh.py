#!/usr/bin/env python3
"""
Auto-Refresh Service
Background service with two separate loops:
- 30s: Update last_balance table from Binance API
- 1h: Create snapshot from last_balance with TWR/P&L calculations
"""
import logging
import threading
import time
from datetime import datetime
from services.session_manager import session_manager
from core.performance_tracker import PerformanceTracker
from db.models import db, LastBalance

logger = logging.getLogger(__name__)


class AutoRefreshService:
    """
    Background service for automatic portfolio refresh and snapshot creation
    Runs two separate threads:
    - Balance update thread: Every 30 seconds
    - Snapshot thread: Every 1 hour
    """

    def __init__(self, app, balance_interval=30, snapshot_interval=3600):
        """
        Initialize auto-refresh service

        Args:
            app: Flask application instance
            balance_interval: Balance update interval in seconds (default: 30)
            snapshot_interval: Snapshot interval in seconds (default: 3600 = 1 hour)
        """
        self.app = app
        self.balance_interval = balance_interval
        self.snapshot_interval = snapshot_interval
        self.balance_refresh_count = 0
        self.snapshot_count = 0
        self.running = False
        self.balance_thread = None
        self.snapshot_thread = None
        self.last_balance_update = None
        self.last_snapshot_time = None

    def start(self):
        """Start the auto-refresh service with both threads"""
        if self.running:
            logger.warning("Auto-refresh service already running")
            return

        self.running = True

        # Start balance update thread
        self.balance_thread = threading.Thread(target=self._balance_update_loop, daemon=True)
        self.balance_thread.start()
        logger.info(f"✅ Balance update thread started (interval: {self.balance_interval}s)")

        # Start snapshot thread
        self.snapshot_thread = threading.Thread(target=self._snapshot_loop, daemon=True)
        self.snapshot_thread.start()
        logger.info(f"✅ Snapshot thread started (interval: {self.snapshot_interval}s)")

    def stop(self):
        """Stop the auto-refresh service"""
        self.running = False
        if self.balance_thread:
            self.balance_thread.join(timeout=5)
        if self.snapshot_thread:
            self.snapshot_thread.join(timeout=5)
        logger.info("🛑 Auto-refresh service stopped")

    def _balance_update_loop(self):
        """Balance update loop - runs every 10 seconds"""
        while self.running:
            try:
                with self.app.app_context():
                    self._update_last_balance()

                # Sleep for interval
                time.sleep(self.balance_interval)

            except Exception as e:
                logger.error(f"❌ Balance update error: {e}")
                time.sleep(self.balance_interval)

    def _snapshot_loop(self):
        """Snapshot creation loop - runs every 30 minutes"""
        while self.running:
            try:
                with self.app.app_context():
                    self._create_snapshot()

                # Sleep for interval
                time.sleep(self.snapshot_interval)

            except Exception as e:
                logger.error(f"❌ Snapshot creation error: {e}")
                time.sleep(self.snapshot_interval)

    def _update_last_balance(self):
        """Fetch balances from Binance and update last_balance table"""
        try:
            trader = session_manager.get_trader()
            balances_data = trader.get_all_balances_usd(min_value=0.0)

            if not balances_data:
                logger.warning("No balances received from Binance")
                return

            # Calculate total USD value for percentages
            total_usd = sum(data['usd_value'] for data in balances_data.values())

            # Update or insert each asset in last_balance table
            timestamp_int = int(datetime.utcnow().strftime('%Y%m%d%H%M'))

            for asset, data in balances_data.items():
                percentage = (data['usd_value'] / total_usd * 100) if total_usd > 0 else 0

                last_balance = LastBalance.query.filter_by(asset=asset).first()

                if last_balance:
                    # Update existing
                    last_balance.balance = data['balance']
                    last_balance.usd_value = data['usd_value']
                    last_balance.percentage = percentage
                    last_balance.timestamp = timestamp_int
                else:
                    # Insert new
                    last_balance = LastBalance(
                        asset=asset,
                        balance=data['balance'],
                        usd_value=data['usd_value'],
                        percentage=percentage,
                        timestamp=timestamp_int
                    )
                    db.session.add(last_balance)

            db.session.commit()

            self.last_balance_update = datetime.utcnow()
            self.balance_refresh_count += 1

            logger.info(f"📊 Balance update #{self.balance_refresh_count}: ${total_usd:.2f} ({len(balances_data)} assets)")

        except Exception as e:
            logger.error(f"Error updating last_balance: {e}")
            db.session.rollback()

    def _create_snapshot(self):
        """Read last_balance and create snapshot with TWR/P&L calculations"""
        try:
            # Get balances from last_balance table
            last_balances = LastBalance.query.all()

            if not last_balances:
                logger.warning("No balances in last_balance table, skipping snapshot")
                return

            # Convert to format expected by PerformanceTracker
            balances = {
                lb.asset: {
                    'balance': lb.balance,
                    'usd_value': lb.usd_value
                }
                for lb in last_balances
            }

            # Use PerformanceTracker to create snapshot with TWR/P&L
            trader = session_manager.get_trader()
            tracker = PerformanceTracker(trader)

            success = tracker.save_current_snapshot(balances=balances)

            if success:
                self.last_snapshot_time = datetime.utcnow()
                self.snapshot_count += 1
                logger.info(f"📸 Snapshot #{self.snapshot_count} created from last_balance")
            else:
                logger.debug("Snapshot creation returned False")

        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")


# Global auto-refresh service instance
auto_refresh_service = None


def start_auto_refresh(app):
    """
    Initialize and start the auto-refresh service

    Args:
        app: Flask application instance
    """
    global auto_refresh_service

    if auto_refresh_service is None:
        balance_interval = app.config.get('BALANCE_UPDATE_INTERVAL', 30)
        snapshot_interval = app.config.get('SNAPSHOT_INTERVAL', 3600)

        auto_refresh_service = AutoRefreshService(app, balance_interval, snapshot_interval)
        auto_refresh_service.start()

    return auto_refresh_service
