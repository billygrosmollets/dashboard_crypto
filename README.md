# Binance Portfolio Manager

A real-time cryptocurrency portfolio tracker with advanced Time-Weighted Return (TWR) analytics and P&L tracking. Monitor your Binance portfolio with automatic updates and professional performance metrics.

![Terminal Theme](https://img.shields.io/badge/Theme-Terminal%20Matrix-00ff41)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Vue](https://img.shields.io/badge/Vue-3.4-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Real-Time Portfolio Tracking**: Automatic balance updates every 30 seconds from Binance API
- **Time-Weighted Return (TWR)**: Professional-grade performance metrics that account for deposits/withdrawals
- **P&L Analytics**: Track profit and loss across multiple time periods (7d, 30d, 90d, total)
- **Historical Snapshots**: Hourly portfolio snapshots with pre-calculated performance metrics
- **Cash Flow Management**: Record deposits and withdrawals for accurate performance tracking
- **Interactive Charts**: Visualize TWR evolution over time with Chart.js
- **Terminal Aesthetic**: Matrix-inspired green-on-black theme with monospace fonts
- **Docker Deployment**: One-command production deployment with Docker Compose

## Tech Stack

**Backend:**
- Flask 3.0 (Python web framework)
- SQLAlchemy (ORM with SQLite)
- python-binance (Binance API client)
- Gunicorn + Gevent (Production WSGI server)

**Frontend:**
- Vue 3 (Composition API)
- Vite (Build tool)
- Pinia (State management)
- Chart.js (Time-series visualization)
- Axios (HTTP client)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Binance API credentials ([Get them here](https://www.binance.com/en/my/settings/api-management))

### Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd dashboard_crypto
```

2. **Configure environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Binance API credentials
# BINANCE_API_KEY=your_api_key_here
# BINANCE_API_SECRET=your_api_secret_here
```

3. **Start Backend**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Unix/Mac
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Backend runs on http://localhost:5000

4. **Start Frontend** (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173

### Production Deployment (Docker)

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at http://localhost

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Binance API                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Auto-Refresh Service                       │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ Balance Thread   │      │ Snapshot Thread  │        │
│  │ Every 30s        │      │ Every 1 hour     │        │
│  └────────┬─────────┘      └────────┬─────────┘        │
└───────────┼─────────────────────────┼──────────────────┘
            │                         │
            ▼                         ▼
┌─────────────────────────────────────────────────────────┐
│                  SQLite Database                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ last_balance │  │  snapshots   │  │  cash_flows  │  │
│  │ (real-time)  │  │ (hourly TWR) │  │ (deposits)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Flask API                             │
│  /api/portfolio/*     /api/performance/*                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Vue 3 Frontend (Pinia)                     │
│  UnifiedDashboard → PortfolioTable + TWRMetrics         │
└─────────────────────────────────────────────────────────┘
```

### Background Service

The application uses a dual-thread background service:

- **Balance Thread** (30s interval): Fetches current balances from Binance and updates the `last_balance` table
- **Snapshot Thread** (1h interval): Reads from `last_balance`, calculates TWR and P&L metrics, creates snapshot in `snapshots` table

This architecture ensures:
- Real-time portfolio data without frontend polling
- Pre-calculated metrics for instant dashboard loading
- Accurate TWR calculations accounting for deposits/withdrawals

### Time-Weighted Return (TWR)

TWR is the industry-standard metric for measuring investment performance. It eliminates the impact of cash flows (deposits/withdrawals) to show pure portfolio performance.

**Formula:** TWR = ∏(1 + Rₚ) - 1

Where Rₚ = (End Value - Adjusted Start) / Adjusted Start

The system:
1. Splits the portfolio timeline into periods based on cash flows
2. Calculates return for each period adjusted for deposits/withdrawals
3. Compounds the returns to get total TWR
4. Annualizes for periods < 365 days

## API Reference

### Portfolio Endpoints

- `GET /api/portfolio/balances` - Get current portfolio balances
- `POST /api/portfolio/refresh` - Trigger refresh (reads from cache)

### Performance Endpoints

- `GET /api/performance/snapshots` - Get all snapshots
- `POST /api/performance/snapshots` - Create manual snapshot
- `GET /api/performance/cashflows` - Get all cash flows
- `POST /api/performance/cashflows` - Add deposit/withdrawal
- `GET /api/performance/twr/:days` - Get TWR for period (0 = total)
- `GET /api/performance/pnl/:days` - Get P&L for period (0 = total)
- `GET /api/performance/stats` - Get tracking statistics
- `GET /api/performance/twr-history?days=30` - Get TWR time-series

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BINANCE_API_KEY` | Binance API key | Required |
| `BINANCE_API_SECRET` | Binance API secret | Required |
| `BINANCE_TESTNET` | Use testnet | `false` |
| `SECRET_KEY` | Flask secret key | Change in production |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost` |
| `DATABASE_URL` | Database path | Auto-configured |
| `BALANCE_UPDATE_INTERVAL` | Balance refresh interval (seconds) | `30` |
| `SNAPSHOT_INTERVAL` | Snapshot interval (seconds) | `3600` |

### Binance API Permissions

Your API key needs:
- ✅ **Read** permission (to fetch balances)
- ❌ **Trade** permission (not required)
- ❌ **Withdraw** permission (not required)

For security, enable IP whitelist and disable trading permissions.

## Database Schema

### Tables

**snapshots**
- `id`: Primary key
- `timestamp`: INTEGER (YYYYMMDDHHmm format)
- `total_value_usd`: Portfolio value in USD
- `twr`: Time-Weighted Return (%)
- `pnl`: Profit/Loss in USD
- `pnl_percent`: P&L percentage

**cash_flows**
- `id`: Primary key
- `timestamp`: INTEGER (YYYYMMDDHHmm format)
- `amount_usd`: Amount (negative for withdrawals)
- `type`: DEPOSIT or WITHDRAW

**last_balance**
- `id`: Primary key
- `timestamp`: INTEGER (YYYYMMDDHHmm format)
- `asset`: Cryptocurrency symbol
- `balance`: Asset quantity
- `usd_value`: USD value
- `percentage`: Portfolio percentage

## Project Structure

```
dashboard_crypto/
├── backend/
│   ├── api/                    # API endpoints (Blueprint)
│   │   ├── portfolio.py        # Portfolio routes
│   │   └── performance.py      # Performance/TWR routes
│   ├── core/                   # Business logic
│   │   ├── binance_trader.py   # Binance API client
│   │   └── performance_tracker.py  # TWR/P&L calculations
│   ├── db/                     # Database
│   │   └── models.py           # SQLAlchemy models
│   ├── services/               # Background services
│   │   ├── auto_refresh.py     # Auto-refresh threads
│   │   └── session_manager.py  # Binance session singleton
│   ├── app.py                  # Flask app factory
│   ├── config.py               # Configuration classes
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # Vue components
│   │   │   ├── UnifiedDashboard.vue
│   │   │   ├── PortfolioTable.vue
│   │   │   ├── TWRMetrics.vue
│   │   │   └── TWRChart.vue
│   │   ├── stores/             # Pinia state
│   │   │   ├── portfolio.js
│   │   │   └── performance.js
│   │   ├── router/             # Vue Router
│   │   └── App.vue             # Root component
│   └── package.json            # Node dependencies
├── docker-compose.yml          # Production deployment
├── Dockerfile.backend          # Backend container
├── .env.example                # Environment template
└── README.md                   # This file
```

## Troubleshooting

### Backend won't start
- Check that port 5000 is not in use
- Verify Binance API credentials in `.env`
- Ensure Python 3.11+ is installed
- Check `backend/portfolio.db` has write permissions

### Frontend shows connection errors
- Ensure backend is running on http://localhost:5000
- Check CORS configuration in `.env` (ALLOWED_ORIGINS)
- Verify no firewall blocking localhost:5000

### TWR showing as null
- Wait for at least 2 snapshots (1+ hours after first run)
- Check that snapshots exist: `GET /api/performance/snapshots`
- Review backend logs for calculation errors

### Docker containers won't start
- Verify `.env` exists with valid credentials
- Check Docker daemon is running
- Review logs: `docker-compose logs -f backend`
- Ensure port 80 is available

## Security Considerations

- **Never commit `.env`** - It contains sensitive API credentials
- **Use IP whitelist** on Binance API settings
- **Disable trading permissions** on API key (only Enable Reading is required)
- **Change SECRET_KEY** in production to a random 32+ character string
- **Use HTTPS** in production (configure reverse proxy like Nginx)
- **Backup `data/portfolio.db`** regularly

## Performance Notes

- **Database**: SQLite is sufficient for single-user deployments. For multi-user, migrate to PostgreSQL
- **Auto-refresh**: Uses single worker to prevent duplicate background threads
- **Cache**: All metrics pre-calculated at snapshot time for instant dashboard loading
- **Polling**: Frontend doesn't poll; displays cached data from `last_balance` table

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [python-binance](https://github.com/sammchardy/python-binance) - Binance API client
- [Chart.js](https://www.chartjs.org/) - Charting library
- [Vue.js](https://vuejs.org/) - Frontend framework
- [Flask](https://flask.palletsprojects.com/) - Backend framework

## Support

For bugs and feature requests, please open an issue on GitHub.

---

**⚠️ Disclaimer:** This software is for informational purposes only. Use at your own risk. Always verify calculations and consult with a financial advisor for investment decisions.
