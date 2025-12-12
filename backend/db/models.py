#!/usr/bin/env python3
"""
SQLAlchemy models for portfolio database
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Snapshot(db.Model):
    """Portfolio snapshot model (replaces snapshots.json)"""
    __tablename__ = 'snapshots'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    total_value_usd = db.Column(db.Float, nullable=False)
    composition = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_composition(self):
        """Parse composition JSON string to dict"""
        return json.loads(self.composition) if self.composition else {}

    def set_composition(self, comp_dict):
        """Set composition from dict"""
        self.composition = json.dumps(comp_dict)

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'total_value_usd': self.total_value_usd,
            'composition': self.get_composition(),
            'created_at': self.created_at.isoformat()
        }


class CashFlow(db.Model):
    """Cash flow model (replaces cashflows.json)"""
    __tablename__ = 'cash_flows'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    amount_usd = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'DEPOSIT' or 'WITHDRAW'
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'amount_usd': self.amount_usd,
            'type': self.type,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


class PortfolioBalance(db.Model):
    """Portfolio balance cache model"""
    __tablename__ = 'portfolio_balances'

    id = db.Column(db.Integer, primary_key=True)
    asset = db.Column(db.String(20), unique=True, nullable=False, index=True)
    balance = db.Column(db.Float, nullable=False)
    free = db.Column(db.Float, nullable=False)
    locked = db.Column(db.Float, nullable=False)
    usd_value = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'asset': self.asset,
            'balance': self.balance,
            'free': self.free,
            'locked': self.locked,
            'usd_value': self.usd_value,
            'percentage': self.percentage,
            'last_updated': self.last_updated.isoformat()
        }


class AllocationSettings(db.Model):
    """Allocation settings model (per-asset allocation)"""
    __tablename__ = 'allocation_settings'

    id = db.Column(db.Integer, primary_key=True)
    allocations = db.Column(db.Text, nullable=False, default='{}')  # JSON: {asset: percent}
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_allocations(self):
        """Parse allocations JSON string to dict"""
        return json.loads(self.allocations) if self.allocations else {}

    def set_allocations(self, allocations_dict):
        """Set allocations from dict"""
        self.allocations = json.dumps(allocations_dict)

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'allocations': self.get_allocations(),
            'updated_at': self.updated_at.isoformat()
        }
