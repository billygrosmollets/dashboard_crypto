# Backend - Binance Portfolio Manager

Backend Flask pour le gestionnaire de portfolio Binance avec API REST, tracking de performance TWR et rebalancing automatique.

## Installation

### Créer l'environnement virtuel

```bash
cd backend
python -m venv venv
```

### Activer l'environnement

**Windows**
```bash
venv\Scripts\activate
```

**Linux/Mac**
```bash
source venv/bin/activate
```

### Installer les dépendances

```bash
pip install -r requirements.txt
```

## Configuration

Le fichier `.env` doit être présent à la **racine du projet** (dossier parent) :

```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_secret
BINANCE_TESTNET=true  # ou false pour production
```

## Démarrage

```bash
python app.py
```

Le serveur démarre sur `http://localhost:5000`

## API Endpoints

### Portfolio

- `GET /api/portfolio/balances` - Récupérer les balances actuelles
- `POST /api/portfolio/refresh` - Forcer un refresh depuis Binance
- `GET /api/portfolio/connection/test` - Tester la connexion Binance

### Performance

- `GET /api/performance/stats` - Métriques TWR (7j, 30j, 90j, 1an, etc.)
- `GET /api/performance/snapshots` - Liste des snapshots
- `POST /api/performance/snapshots` - Créer un snapshot manuel
- `GET /api/performance/cashflows` - Liste des cash flows
- `POST /api/performance/cashflows` - Ajouter un cash flow (dépôt/retrait)

### Rebalancing

- `GET /api/rebalancing/allocation` - Récupérer les allocations cibles
- `POST /api/rebalancing/allocation` - Sauvegarder les allocations cibles
- `POST /api/rebalancing/plan` - Calculer le plan de rebalancing
- `POST /api/rebalancing/execute` - Exécuter le plan de rebalancing

### Health Check

- `GET /health` - Vérifier l'état du serveur

## Architecture

```
backend/
├── api/                        # Blueprints API REST
│   ├── portfolio.py            # Portfolio endpoints
│   ├── performance.py          # Performance tracking endpoints
│   └── rebalancing.py          # Rebalancing endpoints
├── core/                       # Business logic
│   ├── binance_trader.py       # Binance API wrapper
│   ├── performance_tracker.py  # TWR calculations
│   └── portfolio_manager.py    # Rebalancing logic
├── db/                         # Database layer
│   ├── models.py               # SQLAlchemy models (+ session DB)
│   ├── migrations.py           # Migration JSON → SQLite
│   └── schema.sql              # Schéma SQL (référence)
├── services/                   # Background services
│   ├── session_manager.py      # Binance client singleton
│   └── auto_refresh.py         # Auto-refresh service
├── utils/                      # Utilities
│   └── env_loader.py           # Environment loader
├── app.py                      # Flask application
└── config.py                   # Configuration
```

## Base de Données

SQLite (`portfolio.db` à la racine du projet) avec les tables :

### Migration depuis JSON (optionnel)

Si vous avez d'anciens fichiers `snapshots.json` et `cashflows.json` :

```bash
python -m db.migrations
```

Cela migrera automatiquement vos données vers SQLite.

### Tables

**snapshots**
- Snapshots du portfolio (timestamp, total_value_usd, composition)
- Créés automatiquement toutes les 2 heures
- Utilisés pour calculs TWR

**cashflows**
- Dépôts et retraits (timestamp, amount_usd, type, description)
- Permettent de calculer le TWR précisément

**allocation_settings**
- Configuration d'allocation par actif (asset, target_percentage)
- Utilisée pour le rebalancing **par actif** (pas par catégorie)
- Format JSON : `{"allocations": {"BTC": 25.0, "ETH": 15.0, ...}}`

**conversion_history**
- Historique des conversions exécutées
- Utilisé pour tracking des opérations

## Auto-Refresh

Le service auto-refresh tourne en background thread :
- **Portfolio refresh** : Toutes les 60 secondes
- **Snapshots automatiques** : Toutes les 2 heures (120 refreshes)

Le service démarre automatiquement au lancement de `app.py`.

## Business Logic

### BinanceTrader (`core/binance_trader.py`)

Gère toutes les interactions avec l'API Binance :
- Récupération des balances
- Conversions d'actifs (direct, inverse, triangulaire)
- Formatage des quantités selon Binance LOT_SIZE
- Calcul des frais de trading

**Conversion intelligente** :
1. Direct : BTCUSDT
2. Inverse : USDTBTC
3. Triangulaire : BTC → USDT → ETH (via intermédiaire)

### PerformanceTracker (`core/performance_tracker.py`)

Calcule le TWR (Time-Weighted Return) :
- Snapshots périodiques du portfolio
- Cash flows (dépôts/retraits)
- Calculs sur plusieurs périodes : 7j, 14j, 30j, 60j, 90j, 180j, 1an, 2ans, total

### PortfolioManager (`core/portfolio_manager.py`)

Logique de rebalancing :
- Calcul du plan de rebalancing (ACHETER/VENDRE)
- Exécution des trades
- Évitement des conversions USDC ↔ USDC
- Seuil minimum : 0.5% de la valeur du portfolio

## Troubleshooting

### Backend ne démarre pas

**Erreur : "No module named 'flask'"**
```bash
cd backend
pip install -r requirements.txt
```

**Erreur : "Session not initialized"**
- Vérifier que `.env` existe à la racine du projet
- Vérifier `BINANCE_API_KEY` et `BINANCE_API_SECRET`

### Erreurs API Binance

**"Invalid API Key"**
- Vérifier les clés dans `.env`
- Tester avec `GET /api/portfolio/connection/test`

**"Insufficient balance"**
- Vérifier les balances disponibles
- Vérifier que les fonds ne sont pas bloqués dans des ordres

### Database reset

Si vous voulez repartir de zéro :

```bash
# Arrêter le backend
# Supprimer la base
rm ../portfolio.db

# Redémarrer le backend
python app.py
```

La base sera recréée automatiquement au démarrage.

## Notes de Développement

### Threading Model

Toutes les opérations bloquantes (API Binance, calculs TWR) tournent en background threads pour éviter de bloquer le serveur Flask.

### CORS

CORS est activé pour permettre au frontend Vue.js (`localhost:5173`) de communiquer avec le backend.

### Logs

Le backend affiche des logs détaillés :
```
✅ Database initialized
✅ Binance session initialized
✅ Auto-refresh service started (interval: 60s)
📊 Auto-refresh #1: $12345.67 (15 assets)
```
