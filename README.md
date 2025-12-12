# 🚀 Binance Portfolio Manager

Application web moderne pour gérer votre portfolio Binance avec rebalancing automatique, analyse de performance TWR (Time-Weighted Return) et tracking P&L (Profit & Loss).

## Stack Technologique

**Frontend**
- Vue.js 3 (Composition API)
- Pinia (State Management)
- Vite (Build Tool)

**Backend**
- Flask (API REST)
- SQLAlchemy (ORM)
- SQLite (Database)
- python-binance (Binance API)

## Fonctionnalités

- **Portfolio Dashboard** : Visualisation temps réel avec auto-refresh (60s)
- **Rebalancing par actif** : Allocation individuelle par crypto avec exécution automatique des trades
- **TWR Analytics** : Calcul de performance avec Time-Weighted Return sur plusieurs périodes
- **Cash Flows** : Gestion des dépôts/retraits pour calculs de performance précis

## Installation Rapide

### Prérequis

- Python 3.10+
- Node.js 18+
- Compte Binance avec clés API

### Configuration

Copiez `.env.example` vers `.env` et configurez vos clés API :

```bash
cp .env.example .env
```

Éditez `.env` avec vos clés Binance :

```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_secret
BINANCE_TESTNET=true  # ou false pour production
```

### Démarrage

**Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

Le backend démarre sur `http://localhost:5000`

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Le frontend démarre sur `http://localhost:5173`

## Documentation

Pour des instructions détaillées d'installation, d'architecture et de troubleshooting :

- **[Backend Documentation](./backend/README.md)** - API endpoints, architecture backend, database schema
- **[Frontend Documentation](./frontend/README.md)** - Composants Vue, stores Pinia, styling

## Structure du Projet

```
dashboard_crypto/
├── backend/               # Flask API
│   ├── api/              # Endpoints REST
│   │   ├── portfolio.py
│   │   ├── performance.py
│   │   └── rebalancing.py
│   ├── core/             # Business logic
│   │   ├── binance_trader.py
│   │   ├── performance_tracker.py
│   │   └── portfolio_manager.py
│   ├── db/               # Database models
│   │   ├── models.py
│   │   ├── migrations.py
│   │   └── schema.sql
│   ├── services/         # Background services
│   │   ├── session_manager.py
│   │   └── auto_refresh.py
│   ├── utils/            # Utilities
│   │   └── env_loader.py
│   ├── app.py            # Application Flask
│   ├── config.py         # Configuration
│   └── requirements.txt  # Dépendances Python
├── frontend/             # Vue.js SPA
│   ├── src/
│   │   ├── components/  # Composants Vue
│   │   ├── views/       # Pages
│   │   ├── stores/      # Pinia stores
│   │   ├── composables/ # Composables
│   │   └── router/      # Vue Router
│   ├── package.json      # Dépendances Node.js
│   └── vite.config.js    # Configuration Vite
├── .env.example          # Template configuration
├── .env                  # Configuration (à créer depuis .env.example)
├── .gitignore            # Git ignore
└── portfolio.db          # SQLite DB (auto-créée)
```

## Utilisation

### Portfolio & Rebalancing

1. Ouvrez `http://localhost:5173`
2. Éditez les **% Cible** dans le tableau
3. Cliquez sur **Sauvegarder & Calculer Plan**
4. Confirmez pour exécuter les trades

### TWR Analytics

1. Cliquez sur **TWR Analytics** dans la sidebar
2. Visualisez vos performances (7j, 30j, 90j, 1an, etc.)
3. Ajoutez des cash flows pour tracking précis

## Auto-Refresh

- **Portfolio** : 60 secondes
- **Performance** : 120 secondes
- **Snapshots** : Toutes les 2 heures (automatique)

## Support

Pour des problèmes techniques, consultez :
- [Backend Troubleshooting](./backend/README.md#troubleshooting)
- [Frontend Troubleshooting](./frontend/README.md#troubleshooting)
