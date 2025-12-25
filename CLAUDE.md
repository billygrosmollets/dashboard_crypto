# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Binance Portfolio Manager - A cryptocurrency portfolio tracker with Time-Weighted Return (TWR) analytics and P&L tracking. Built with Vue 3 + Vite frontend and Flask + SQLAlchemy backend.

## Development Commands

### Backend (Flask)

```bash
# Setup
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix
pip install -r requirements.txt

# Configure
# Copy .env.example to .env and add Binance API credentials

# Run development server
python app.py
# Server runs on http://localhost:5000
```

### Frontend (Vue 3 + Vite)

```bash
# Setup
cd frontend
npm install

# Development server
npm run dev
# Server runs on http://localhost:5173

# Production build
npm run build
# Output in frontend/dist/
```

### Docker Production

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

## Architecture

### Backend Architecture

**Database Models** (backend/db/models.py):
- `Snapshot`: Portfolio snapshots taken hourly with pre-calculated TWR/P&L metrics
  - Timestamp stored as INTEGER in YYYYMMDDHHmm format
  - TWR and P&L calculated from inception at snapshot time
- `CashFlow`: Deposits/withdrawals for TWR calculations
- `LastBalance`: Real-time portfolio balances updated every 30 seconds

**Core Components**:
- `BinanceTrader` (backend/core/binance_trader.py): Fetches balances from Binance API
- `PerformanceTracker` (backend/core/performance_tracker.py): TWR and P&L calculation engine
  - TWR calculation uses cash-flow-adjusted periods (lines 126-220)
  - Simple P&L: (Current - Initial) - Net Cash Flow (lines 274-390)
- `SessionManager` (backend/services/session_manager.py): Singleton for Binance client lifecycle
- `AutoRefreshService` (backend/services/auto_refresh.py): Background service with two threads:
  - Balance update: Every 30s, updates `last_balance` table from Binance
  - Snapshot creation: Every 1 hour, creates snapshot from `last_balance` with TWR/P&L

**API Endpoints**:
- `/api/portfolio/balances` - Get current portfolio from `last_balance` table
- `/api/portfolio/refresh` - Read fresh balances (actual refresh happens in background)
- `/api/performance/snapshots` - CRUD operations for snapshots
- `/api/performance/cashflows` - CRUD operations for cash flows
- `/api/performance/twr/:days` - Calculate TWR for period (0 = total)
- `/api/performance/pnl/:days` - Calculate P&L for period (0 = total)
- `/api/performance/stats` - Tracking statistics
- `/api/performance/twr-history` - TWR evolution for charts

**Configuration** (backend/config.py):
- `DevelopmentConfig`: SQLite in backend/portfolio.db
- `ProductionConfig`: SQLite in data/portfolio.db
- Auto-refresh intervals: 30s for balances, 3600s (1h) for snapshots

### Frontend Architecture

**State Management** (Pinia stores):
- `portfolio.js`: Manages balances from `last_balance` table
- `performance.js`: Manages snapshots, cash flows, TWR, and P&L metrics

**Routing**:
- Single page app with unified dashboard at `/`
- Router defined in frontend/src/router/index.js

**Key Components**:
- `UnifiedDashboard.vue`: Main dashboard view
- `PortfolioTable.vue`: Real-time portfolio balances
- `TWRMetrics.vue`: Performance metrics display
- `TWRChart.vue`: Chart.js time-series visualization
- `CashFlowForm.vue`: Add deposits/withdrawals
- `MetricCard.vue`: Reusable metric display card
- `UTCClock.vue`: UTC time display

**Styling**:
- Terminal/Matrix theme (green on black)
- CSS variables in App.vue root scope
- Monospace fonts throughout

### Data Flow

1. **Background Updates**: AutoRefreshService runs two threads
   - Every 30s: Fetch balances from Binance → Update `last_balance` table
   - Every 1h: Read `last_balance` → Create snapshot with TWR/P&L in `snapshots` table

2. **Frontend Queries**: All data served from database tables
   - Portfolio: Read from `last_balance` table
   - Metrics: Read pre-calculated values from `snapshots` table
   - Charts: Query `snapshots` table for time-series data

3. **TWR Calculation**: Performed at snapshot creation time
   - Splits portfolio into periods based on cash flows
   - Calculates period returns adjusted for deposits/withdrawals
   - Compounds returns: TWR = ∏(1 + period_return) - 1

4. **User Actions**:
   - Add cash flow → Stored in `cash_flows` → Affects next snapshot TWR calculation
   - Manual snapshot → Reads `last_balance` → Calculates TWR/P&L → Saves to `snapshots`

## Important Implementation Details

### Timestamp Format
All database timestamps use INTEGER format YYYYMMDDHHmm (e.g., 202512210145 for Dec 21, 2025 01:45). Convert using:
- `PerformanceTracker.timestamp_to_datetime(int)` → datetime
- `PerformanceTracker.datetime_to_timestamp(dt)` → int

### TWR Calculation Preservation
The TWR calculation logic in `PerformanceTracker.calculate_twr()` (lines 126-220) is the core algorithm. When modifying performance tracking:
- Preserve the cash-flow-adjusted period splitting logic
- Maintain the cumulative return multiplication
- Keep the adjusted_start calculation: start_value + cash_flow

### Auto-Refresh Single Worker
Production uses Gunicorn with `--workers 1` to prevent duplicate auto-refresh threads. This ensures only one background service updates the database.

### Development Mode Flask Reloader
Development mode disables Flask debug reloader (DEBUG=False) to avoid SQLite locking issues. Use `WERKZEUG_RUN_MAIN` check in app.py:100-108 to start auto-refresh only in main process.

### SQLAlchemy Session Management
Use Flask's application context (`with app.app_context()`) for all database operations in background threads. Always commit or rollback explicitly.

## Environment Variables

Required in `.env` file (see `.env.example`):
- `BINANCE_API_KEY`: Binance API key
- `BINANCE_API_SECRET`: Binance API secret
- `BINANCE_TESTNET`: true/false for testnet mode
- `SECRET_KEY`: Flask secret key (min 32 chars for production)
- `ALLOWED_ORIGINS`: Comma-separated CORS origins
- `DATABASE_URL`: SQLite path (optional, defaults per config)

## Database

SQLite database with three tables (see backend/db/models.py):
- `snapshots`: Portfolio snapshots with pre-calculated metrics
- `cash_flows`: Deposits and withdrawals
- `last_balance`: Current real-time balances

Database location:
- Development: backend/portfolio.db
- Production: data/portfolio.db (mounted Docker volume)

Migrations: None (using `db.create_all()` for schema creation)
