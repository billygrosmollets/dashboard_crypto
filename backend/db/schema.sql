-- ============================================================================
-- Binance Portfolio Manager - Database Schema
-- ============================================================================

-- Snapshots table (replaces snapshots.json)
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    total_value_usd REAL NOT NULL,
    composition TEXT NOT NULL,  -- JSON string with portfolio composition
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cash flows table (replaces cashflows.json)
CREATE TABLE IF NOT EXISTS cash_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    amount_usd REAL NOT NULL,
    type TEXT CHECK(type IN ('DEPOSIT', 'WITHDRAW')) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio balances table (cached current state for fast access)
CREATE TABLE IF NOT EXISTS portfolio_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset TEXT UNIQUE NOT NULL,
    balance REAL NOT NULL,
    free REAL NOT NULL,
    locked REAL NOT NULL,
    usd_value REAL NOT NULL,
    percentage REAL NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Allocation settings table (new category-based allocation)
CREATE TABLE IF NOT EXISTS allocation_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    btc_percent REAL DEFAULT 33.33,
    altcoin_percent REAL DEFAULT 33.33,
    stablecoin_percent REAL DEFAULT 33.34,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Conversion history table (for tracking and analysis)
CREATE TABLE IF NOT EXISTS conversion_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    from_asset TEXT NOT NULL,
    to_asset TEXT NOT NULL,
    amount REAL NOT NULL,
    result_amount REAL,
    fee_usd REAL,
    conversion_type TEXT,  -- 'direct' or 'triangular'
    status TEXT,  -- 'SUCCESS' or 'FAILED'
    error_message TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp);
CREATE INDEX IF NOT EXISTS idx_cashflows_timestamp ON cash_flows(timestamp);
CREATE INDEX IF NOT EXISTS idx_portfolio_balances_asset ON portfolio_balances(asset);
CREATE INDEX IF NOT EXISTS idx_conversion_history_timestamp ON conversion_history(timestamp);
