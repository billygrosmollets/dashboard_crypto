#!/usr/bin/env python3
"""
SQLAlchemy models for portfolio database
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Snapshot(db.Model):
    """Portfolio snapshot model"""
    __tablename__ = 'snapshots'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Integer, nullable=False, index=True)  # YYYYMMDDHHmm
    total_value_usd = db.Column(db.Integer, nullable=False)  # Dollars (no cents)
    
    # Performance metrics (calculated from inception)
    twr = db.Column(db.Float, nullable=True)  # Time-Weighted Return % (2 decimals)
    pnl = db.Column(db.Integer, nullable=True)  # P&L in USD (no cents)
    pnl_percent = db.Column(db.Float, nullable=True)  # P&L % (2 decimals)

    def to_dict(self):
        """Convert to dictionary for API response"""
        # Convert timestamp 202512210145 to ISO string "2025-12-21T01:45:00"
        timestamp_str = str(self.timestamp)
        dt = datetime(
            year=int(timestamp_str[0:4]),
            month=int(timestamp_str[4:6]),
            day=int(timestamp_str[6:8]),
            hour=int(timestamp_str[8:10]),
            minute=int(timestamp_str[10:12])
        )

        return {
            'id': self.id,
            'timestamp': dt.isoformat(),
            'total_value_usd': float(self.total_value_usd) if self.total_value_usd else 0.0,
            'twr': round(self.twr, 4) if self.twr is not None else None,
            'pnl': float(self.pnl) if self.pnl is not None else None,
            'pnl_percent': round(self.pnl_percent, 4) if self.pnl_percent is not None else None
        }


class CashFlow(db.Model):
    """Cash flow model"""
    __tablename__ = 'cash_flows'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Integer, nullable=False, index=True)  # YYYYMMDDHHmm
    amount_usd = db.Column(db.Integer, nullable=False)  # Dollars (no cents)
    type = db.Column(db.String(20), nullable=False)  # 'DEPOSIT' or 'WITHDRAW'

    def to_dict(self):
        """Convert to dictionary for API response"""
        # Convert timestamp
        timestamp_str = str(self.timestamp)
        dt = datetime(
            year=int(timestamp_str[0:4]),
            month=int(timestamp_str[4:6]),
            day=int(timestamp_str[6:8]),
            hour=int(timestamp_str[8:10]),
            minute=int(timestamp_str[10:12])
        )

        return {
            'id': self.id,
            'timestamp': dt.isoformat(),
            'amount_usd': float(self.amount_usd),
            'type': self.type
        }


class LastBalance(db.Model):
    """Current portfolio balance (updated every 10 seconds)"""
    __tablename__ = 'last_balance'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Integer, nullable=False, index=True)  # YYYYMMDDHHmm (consistent with other tables)
    asset = db.Column(db.String(20), unique=True, nullable=False, index=True)
    balance = db.Column(db.Float, nullable=False)
    usd_value = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """Convert to dictionary for API response"""
        # Convert timestamp
        timestamp_str = str(self.timestamp)
        dt = datetime(
            year=int(timestamp_str[0:4]),
            month=int(timestamp_str[4:6]),
            day=int(timestamp_str[6:8]),
            hour=int(timestamp_str[8:10]),
            minute=int(timestamp_str[10:12])
        )

        return {
            'asset': self.asset,
            'balance': round(self.balance, 4),
            'usd_value': round(self.usd_value, 4),
            'percentage': round(self.percentage, 4),
            'timestamp': dt.isoformat()
        }
