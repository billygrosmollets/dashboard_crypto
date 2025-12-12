#!/usr/bin/env python3
"""
Migration script: JSON files → SQLite database
Migrates snapshots.json and cashflows.json to database tables
"""
import json
import os
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def migrate_json_to_sqlite(app):
    """
    Migrate existing snapshots.json and cashflows.json to SQLite database

    Args:
        app: Flask application instance with app context
    """
    from db.models import db, Snapshot, CashFlow

    # Paths to JSON files (in parent directory)
    base_dir = Path(__file__).parent.parent.parent
    snapshots_file = base_dir / 'snapshots.json'
    cashflows_file = base_dir / 'cashflows.json'

    with app.app_context():
        # Create all tables
        db.create_all()
        logger.info("✅ Database tables created")

        # Migrate snapshots.json
        if snapshots_file.exists():
            try:
                with open(snapshots_file, 'r', encoding='utf-8') as f:
                    snapshots_data = json.load(f)

                logger.info(f"📸 Migrating {len(snapshots_data)} snapshots...")

                for snap in snapshots_data:
                    # Check if snapshot already exists (avoid duplicates)
                    existing = Snapshot.query.filter_by(
                        timestamp=datetime.fromisoformat(snap['timestamp'])
                    ).first()

                    if not existing:
                        snapshot = Snapshot(
                            timestamp=datetime.fromisoformat(snap['timestamp']),
                            total_value_usd=snap['total_value_usd']
                        )
                        snapshot.set_composition(snap['composition'])
                        db.session.add(snapshot)

                db.session.commit()
                logger.info(f"✅ Migrated {len(snapshots_data)} snapshots")

            except Exception as e:
                logger.error(f"❌ Error migrating snapshots: {e}")
                db.session.rollback()
        else:
            logger.warning(f"⚠️  Snapshots file not found: {snapshots_file}")

        # Migrate cashflows.json
        if cashflows_file.exists():
            try:
                with open(cashflows_file, 'r', encoding='utf-8') as f:
                    cashflows_data = json.load(f)

                logger.info(f"💰 Migrating {len(cashflows_data)} cash flows...")

                for cf in cashflows_data:
                    # Check if cash flow already exists (avoid duplicates)
                    existing = CashFlow.query.filter_by(
                        timestamp=datetime.fromisoformat(cf['timestamp']),
                        amount_usd=cf['amount_usd']
                    ).first()

                    if not existing:
                        cashflow = CashFlow(
                            timestamp=datetime.fromisoformat(cf['timestamp']),
                            amount_usd=cf['amount_usd'],
                            type=cf['type'],
                            description=cf.get('description', '')
                        )
                        db.session.add(cashflow)

                db.session.commit()
                logger.info(f"✅ Migrated {len(cashflows_data)} cash flows")

            except Exception as e:
                logger.error(f"❌ Error migrating cash flows: {e}")
                db.session.rollback()
        else:
            logger.warning(f"⚠️  Cash flows file not found: {cashflows_file}")

        # Create default allocation settings if not exists
        from db.models import AllocationSettings
        if not AllocationSettings.query.first():
            default_allocation = AllocationSettings(
                btc_percent=33.33,
                altcoin_percent=33.33,
                stablecoin_percent=33.34
            )
            db.session.add(default_allocation)
            db.session.commit()
            logger.info("✅ Created default allocation settings")

        logger.info("🎉 Migration completed successfully!")

        # Print stats
        snapshot_count = Snapshot.query.count()
        cashflow_count = CashFlow.query.count()
        logger.info(f"📊 Database stats:")
        logger.info(f"   - Snapshots: {snapshot_count}")
        logger.info(f"   - Cash flows: {cashflow_count}")


if __name__ == '__main__':
    """Run migration standalone"""
    from pathlib import Path
    import sys

    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from app import create_app

    # Set UTF-8 encoding for console output
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    logging.basicConfig(level=logging.INFO)
    app = create_app()

    print("=" * 60)
    print("🔄 Starting JSON to SQLite migration...")
    print("=" * 60)

    migrate_json_to_sqlite(app)

    print("=" * 60)
    print("✅ Migration complete!")
    print("=" * 60)
