#!/usr/bin/env python3
"""
Auto-Refresh Service
Background service that refreshes portfolio every 60 seconds
Matches the behavior of the original Tkinter app
"""
import logging
import threading
import time
from datetime import datetime
from services.session_manager import session_manager
from db.models import db, PortfolioBalance, Snapshot

logger = logging.getLogger(__name__)


class AutoRefreshService:
    """
    Background service for automatic portfolio refresh
    Runs in a separate thread and updates the database every 60 seconds
    """

    def __init__(self, app, interval=60, snapshot_interval=120):
        """
        Initialize auto-refresh service

        Args:
            app: Flask application instance
            interval: Refresh interval in seconds (default: 60)
            snapshot_interval: Take snapshot every N refreshes (default: 120 = 2 hours)
        """
        self.app = app
        self.interval = interval
        self.snapshot_interval = snapshot_interval
        self.refresh_count = 0
        self.running = False
        self.thread = None

    def start(self):
        """Start the auto-refresh service in a background thread"""
        if self.running:
            logger.warning("Auto-refresh service already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()
        logger.info(f"✅ Auto-refresh service started (interval: {self.interval}s)")

    def stop(self):
        """Stop the auto-refresh service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🛑 Auto-refresh service stopped")

    def _refresh_loop(self):
        """Main refresh loop running in background thread"""
        while self.running:
            try:
                with self.app.app_context():
                    self._refresh_portfolio()

                # Sleep for interval
                time.sleep(self.interval)

            except Exception as e:
                logger.error(f"❌ Auto-refresh error: {e}")
                # Continue running even on error
                time.sleep(self.interval)

    def _refresh_portfolio(self):
        """Refresh portfolio from Binance API and update database"""
        try:
            # Get trader instance
            trader = session_manager.get_trader()

            # Get fresh balances
            fresh_balances = trader.get_all_balances_usd(5.0)

            if not fresh_balances:
                logger.warning("No balances found above $5 threshold")
                return

            # Calculate total
            total_value_usd = sum(data['usd_value'] for data in fresh_balances.values())

            # Update database cache
            PortfolioBalance.query.delete()

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

            # Increment refresh counter
            self.refresh_count += 1

            # Take snapshot every snapshot_interval refreshes (e.g., every 120 refreshes = 2 hours)
            if self.refresh_count % self.snapshot_interval == 0:
                self._take_snapshot(fresh_balances, total_value_usd)

            logger.info(f"📊 Auto-refresh #{self.refresh_count}: ${total_value_usd:.2f} ({len(fresh_balances)} assets)")

        except RuntimeError as e:
            logger.error(f"Session not initialized: {e}")
        except Exception as e:
            logger.error(f"Error refreshing portfolio: {e}")
            db.session.rollback()

    def _take_snapshot(self, balances, total_value_usd):
        """
        Take a snapshot of the current portfolio
        Matches the behavior of original app (snapshot every 2 hours)

        Args:
            balances: Fresh balances dict from Binance
            total_value_usd: Total portfolio value
        """
        try:
            # Compose snapshot data
            composition = {}
            for asset, data in balances.items():
                if data['usd_value'] > 1.0:  # Only save significant positions
                    composition[asset] = {
                        'balance': data['balance'],
                        'usd_value': data['usd_value'],
                        'percentage': (data['usd_value'] / total_value_usd * 100) if total_value_usd > 0 else 0
                    }

            # Create snapshot
            snapshot = Snapshot(
                timestamp=datetime.utcnow(),
                total_value_usd=total_value_usd
            )
            snapshot.set_composition(composition)

            db.session.add(snapshot)
            db.session.commit()

            logger.info(f"📸 Snapshot saved: ${total_value_usd:.2f} (refresh #{self.refresh_count})")

        except Exception as e:
            logger.error(f"Error taking snapshot: {e}")
            db.session.rollback()


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
        interval = app.config.get('AUTO_REFRESH_INTERVAL', 60)
        snapshot_interval = app.config.get('SNAPSHOT_INTERVAL', 120)

        auto_refresh_service = AutoRefreshService(app, interval, snapshot_interval)
        auto_refresh_service.start()

    return auto_refresh_service
