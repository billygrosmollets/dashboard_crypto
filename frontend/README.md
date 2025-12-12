# Frontend - Binance Portfolio Manager

Frontend Vue.js 3 pour le gestionnaire de portfolio Binance avec dashboard en temps réel, rebalancing et analytics TWR.

## Installation

```bash
cd frontend
npm install
```

## Développement

```bash
npm run dev
```

Le frontend démarre sur `http://localhost:5173` (port par défaut de Vite).

## Build Production

```bash
# Compiler pour la production
npm run build

# Prévisualiser le build de production
npm run preview
```

## Architecture

```
frontend/src/
├── main.js                     # Point d'entrée Vue
├── App.vue                     # Composant racine + layout
├── router/                     # Vue Router
│   └── index.js                # Routes de l'app
├── stores/                     # Pinia state management
│   ├── portfolio.js            # Portfolio & allocations par actif
│   ├── rebalancing.js          # Rebalancing par catégorie (legacy, non utilisé)
│   └── performance.js          # TWR analytics
├── views/                      # Vues (pages)
│   ├── PortfolioView.vue       # Dashboard portfolio + rebalancing
│   └── TWRAnalyticsView.vue    # Analytics de performance
├── components/                 # Composants réutilisables
│   ├── PortfolioTable.vue      # Table portfolio avec rebalancing intégré
│   ├── RebalancingModal.vue    # Modal de confirmation du plan
│   ├── LogsPanel.vue           # Logs d'exécution
│   ├── TWRMetrics.vue          # Cartes de métriques TWR
│   ├── CashFlowForm.vue        # Formulaire cash flows
│   ├── AllocationConfig.vue    # (Legacy - non utilisé actuellement)
│   └── RebalancingPanel.vue    # (Legacy - non utilisé actuellement)
├── composables/                # Composition API hooks
│   ├── usePolling.js           # HTTP polling hook
│   └── useAPI.js               # API wrapper avec axios
└── assets/
    └── styles/
        └── main.css            # Styles globaux
```

## Fonctionnalités

### Portfolio Dashboard

- Affichage des balances en temps réel
- Auto-refresh toutes les 60 secondes (HTTP polling)
- Tri par valeur USD décroissante
- Affichage total du portfolio
- Balance libre/bloquée par actif
- Rafraîchissement manuel

### Rebalancing (intégré dans PortfolioTable)

- **Allocation par actif** (pas par catégorie)
- Édition des allocations cibles (% Cible) directement dans le tableau
- Auto-remplissage avec allocation actuelle
- Validation en temps réel (total doit être 100%)
- Calcul automatique des écarts (% Écart)
- Modal de confirmation du plan
- Exécution automatique des trades
- Logs d'exécution en temps réel

### TWR Analytics

- Métriques de performance sur plusieurs périodes (7j, 14j, 30j, 60j, 90j, 180j, 1an, 2ans, total)
- Création de snapshots manuels
- Ajout de cash flows (dépôts/retraits)
- Auto-refresh toutes les 120 secondes

## API Backend

Le frontend communique avec le backend Flask via proxy Vite :

```javascript
// Configuration Vite (vite.config.js)
proxy: {
  '/api': {
    target: 'http://localhost:5000',  // Flask backend
    changeOrigin: true
  }
}
```

### Endpoints utilisés

**Portfolio**
- `GET /api/portfolio/balances` - Récupérer les balances
- `POST /api/portfolio/refresh` - Forcer un refresh
- `GET /api/portfolio/connection/test` - Tester la connexion

**Performance**
- `GET /api/performance/stats` - Métriques TWR
- `GET /api/performance/snapshots` - Liste des snapshots
- `POST /api/performance/snapshots` - Créer un snapshot
- `GET /api/performance/cashflows` - Liste des cash flows
- `POST /api/performance/cashflows` - Ajouter un cash flow

**Rebalancing**
- `GET /api/rebalancing/allocation` - Récupérer les allocations
- `POST /api/rebalancing/allocation` - Sauvegarder les allocations
- `POST /api/rebalancing/plan` - Calculer le plan
- `POST /api/rebalancing/execute` - Exécuter les trades

## State Management (Pinia)

### Portfolio Store (`stores/portfolio.js`)

Gère :
- Balances du portfolio
- Valeur totale USD
- Allocations cibles (% par actif)
- Plan de rebalancing
- Logs d'exécution
- État de chargement et erreurs

Actions principales :
- `fetchBalances()` - Récupérer les balances
- `refreshPortfolio()` - Forcer un refresh
- `saveAllocation()` - Sauvegarder les allocations
- `calculatePlan()` - Calculer le plan de rebalancing
- `executePlan()` - Exécuter les trades

### Performance Store (`stores/performance.js`)

Gère :
- Métriques TWR (toutes les périodes)
- Liste des snapshots
- Liste des cash flows
- État de chargement et erreurs

Actions principales :
- `fetchPerformanceStats()` - Récupérer les métriques
- `createSnapshot()` - Créer un snapshot
- `addCashFlow()` - Ajouter un cash flow
- `refreshAllData()` - Tout rafraîchir

## Composables

### usePolling (`composables/usePolling.js`)

Hook pour HTTP polling automatique :
```javascript
usePolling(async () => {
  await portfolioStore.fetchBalances()
}, 60000) // 60 secondes
```

- S'exécute immédiatement au montage
- Se nettoie automatiquement au démontage
- Utilise `setInterval` en interne

### useAPI (`composables/useAPI.js`)

Wrapper axios avec gestion d'erreurs centralisée.

## Styling

**Design System** : Dark Pro avec Glassmorphism

**Palette de couleurs** :
```css
--bg-primary: #0a0a0a;           /* Fond principal */
--glass-bg: rgba(28, 28, 28, 0.7); /* Fond glassmorphism */
--glass-border: rgba(255, 215, 0, 0.15); /* Bordures */
--gold-primary: #d4af37;          /* Or principal */
--gold-secondary: #f0d26f;        /* Or secondaire */
--gray-700: #c0c0c0;              /* Texte principal */
--gray-800: #d0d0d0;              /* Texte emphase */
```

**Effets glassmorphism** :
- `backdrop-filter: blur(20px)` sur les cartes
- Bordures semi-transparentes avec reflets dorés
- Ombres subtiles `box-shadow: 0 8px 32px`

## Troubleshooting

### Frontend ne démarre pas

**Erreur : "Cannot find module"**
```bash
cd frontend
npm install
```

**Port 5173 déjà utilisé**
```bash
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5173 | xargs kill -9
```

### Erreurs de connexion backend

**Erreur CORS**
- Vérifier que le backend tourne sur `http://localhost:5000`
- Ouvrir `http://localhost:5173` (pas 3000)

**Page blanche**
- Ouvrir la console (F12) et vérifier les erreurs
- Vérifier que `npm install` a bien été exécuté
- Vérifier que le backend est démarré

### Problèmes de rebalancing

**"Le total doit être égal à 100%"**
- Vérifier que la somme des % Cible fait exactement 100%
- Utiliser le bouton "Auto-remplir" pour remplir automatiquement

**"Erreur lors du calcul du plan"**
- Vérifier que les allocations sont sauvegardées (bouton "Sauvegarder & Calculer Plan")
- Vérifier les logs backend pour détails

## Dev Notes

### Proxy Vite

Toutes les requêtes vers `/api` sont automatiquement proxifiées vers `http://localhost:5000` en développement.

### Hot Module Replacement (HMR)

Vite utilise HMR pour un rechargement instantané lors des modifications de code.

### Build Production

Le build de production génère des assets optimisés dans `dist/` :
```bash
npm run build
# Fichiers générés dans dist/
```

### Composants et Stores Legacy

⚠️ **Note** : Certains fichiers sont présents mais non utilisés dans l'UI actuelle :
- `stores/rebalancing.js` - Store pour rebalancing par catégorie (BTC/Altcoins/Stablecoins)
- `components/AllocationConfig.vue` - Ancien composant de configuration
- `components/RebalancingPanel.vue` - Ancien panel de rebalancing

L'implémentation actuelle utilise un rebalancing **par actif individuel** intégré directement dans `PortfolioTable.vue` avec le store `portfolio.js`.
