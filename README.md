# 🚀 Binance Portfolio Manager

Une application Python GUI complète pour la gestion de portefeuille crypto avec conversion multi-actifs et analytics de performance sur Binance.

## ✨ Fonctionnalités

### 🔑 Connexion Sécurisée
- Configuration simple via fichier `.env`
- Support mode testnet pour tests sans risque
- Chargement automatique des clés API

### 💰 Affichage Portfolio
- Affichage de tous les actifs > 5$ USD
- Calcul automatique des valeurs en USD
- Pourcentage de répartition du portfolio
- Distinction fonds libres/bloqués
- Auto-refresh toutes les 10 secondes

### 🔄 Convertisseur Crypto Universal
- **Conversion multi-actifs** : N'importe quel actif vers un autre
- **Routes intelligentes** :
  - Conversion directe si paire disponible
  - Conversion inverse automatique
  - Conversion triangulaire via USDT, BUSD, BTC
- **Interface intuitive** : ComboBox "De" avec actifs possédés seulement
- **Calcul des frais** : Affichage détaillé des frais de conversion

### ⚖️ Rééquilibrage Portfolio
- **Répartition personnalisée** : % BTC, % USDC, % Altcoins
- **Rééquilibrage intelligent** :
  - Calcul automatique des actions nécessaires
  - Évite les conversions inutiles entre stablecoins
  - Répartition équilibrée automatique des altcoins
- **Suivi des frais** : Calcul et affichage des coûts de rééquilibrage

### 📊 Performance Analytics (TWR)
- **Time-Weighted Return** : Performance pure indépendante du timing
- **Snapshots automatiques** : Sauvegarde périodique du portfolio
- **Benchmarking** : Comparaison vs BTC et ETH
- **Alpha** : Mesure de l'outperformance
- **Base de données SQLite** : Historique complet des performances

## 🚦 Installation Rapide

### 1. Prérequis
- Python 3.7+
- Clés API Binance

### 2. Installation
```bash
# Cloner le projet
git clone <votre-repo>
cd btc-usdc-converter

# Environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Installation des dépendances
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Créer et éditer le fichier .env
BINANCE_API_KEY=votre_cle_api_ici
BINANCE_API_SECRET=votre_secret_ici
BINANCE_TESTNET=true  # false pour trading réel
```

### 4. Lancement
```bash
python main.py
```

## 🎯 Guide d'Utilisation

### Configuration Initiale
1. **Éditez `.env`** avec vos clés API Binance
2. **Activez testnet** pour commencer (`BINANCE_TESTNET=true`)
3. **Lancez l'app** et testez la connexion

### Sections Principales

#### 📊 Performance Analytics
- **Tracking automatique** : Snapshots périodiques du portfolio
- **Métriques disponibles** : TWR 7j, 30j, 90j selon l'historique
- **Benchmarking** : Comparaison avec BTC et ETH (30j minimum)
- **Base de données** : Stockage local des données (performance.db)

#### ⚖️ Configuration Portfolio
- **Allocation personnalisée** : Définir % BTC, USDC, Altcoins
- **Rééquilibrage en un clic** : Actions automatiques calculées
- **Évitement des frais** : Pas de conversion entre stablecoins
- **Suivi des coûts** : Affichage détaillé des frais de rééquilibrage

#### 🔄 Convertisseur Crypto
- **Interface simplifiée** : Seulement vos actifs possédés en source
- **Conversion intelligente** : Routes optimales automatiques
- **Calcul de frais** : Estimation avant exécution
- **Support triangulaire** : Via USDT/BUSD/BTC si nécessaire

#### 💰 Portfolio
- **Vue d'ensemble** : Tous vos actifs avec valeurs USD
- **Auto-refresh** : Mise à jour toutes les 10 secondes
- **Tri par valeur** : Actifs les plus importants en premier

### Exemple de Rééquilibrage

**Situation :**
- Portfolio : $10,000
- Actuel : 10% BTC, 50% USDC, 40% ETH
- Objectif : 25% BTC, 40% USDC, 35% altcoins

**Actions automatiques :**
- Acheter $1,500 de BTC (10% → 25%)
- Vendre $1,000 de USDC (50% → 40%)
- Conserver ETH dans la répartition altcoins

## 🔒 Sécurité

### Configuration API Binance
1. [Binance](https://www.binance.com) → **Profil** → **Sécurité API**
2. **Créer API Key** avec permissions **Spot Trading uniquement**
3. **Testez avec testnet** d'abord : [testnet.binance.vision](https://testnet.binance.vision/)

### Bonnes Pratiques
- ✅ Permissions limitées (Spot Trading seulement)
- ✅ Mode testnet pour apprendre
- ✅ Commencer avec petits montants
- ✅ Fichier `.env` dans `.gitignore`
- ⚠️ Ne jamais partager vos clés API

## 📁 Structure

```
btc-usdc-converter/
├── main.py                 # Application principale + interface GUI
├── config_converter.py     # Configuration portfolio + convertisseur
├── performance_tracker.py  # Analytics TWR + base de données
├── .env                   # Configuration API (à créer)
├── requirements.txt       # Dépendances Python
├── README.md             # Documentation
├── .gitignore           # Fichiers à ignorer
└── performance.db       # Base de données SQLite (créée auto)
```

## 🔧 Architecture

### Modules Principaux
- **main.py** :
  - `TradingApp` : Interface GUI principale
  - `BinanceTrader` : API Binance + conversions intelligentes
  - `PortfolioManager` : Logique de rééquilibrage
  - `EnvLoader` : Chargement sécurisé des variables

- **config_converter.py** :
  - `PortfolioConfig` : Interface de configuration et rééquilibrage
  - `CryptoConverter` : Convertisseur crypto universal

- **performance_tracker.py** :
  - `PerformanceTracker` : Calculs TWR et métriques
  - `PerformanceDatabase` : Gestion SQLite
  - `PerformanceInterface` : Interface utilisateur analytics

### Fonctionnalités Techniques
- **Conversion triangulaire** automatique via USDT/BUSD/BTC
- **Calcul intelligent** des routes de trading optimales
- **Formatage précis** des quantités selon Binance
- **Threading** pour interface réactive
- **Base de données SQLite** pour historique performances
- **Gestion d'erreurs** robuste avec logging

## 🐛 Dépannage

### Erreurs Courantes
```bash
# Connexion API
→ Vérifiez vos clés dans .env
→ Testez en mode testnet d'abord

# Balance insuffisante
→ Actualisez les balances
→ Vérifiez les montants disponibles

# Erreur de conversion
→ Vérifiez que la paire existe sur Binance
→ Minimum de trading respecté
```

### Logs
L'application affiche des logs détaillés dans la console pour diagnostiquer les problèmes.

## 🎉 Avantages

### Pour Débutants
- Interface intuitive avec onglets
- Profils de risque prédéfinis
- Mode testnet sécurisé
- Simulation avant exécution

### Pour Traders Expérimentés
- Conversion multi-actifs avancée
- Rééquilibrage automatique
- Analyse détaillée du portfolio
- Routes de trading optimisées

### Gestion Passive
- Maintien automatique de l'allocation
- Répartition équilibrée des altcoins
- Rééquilibrage en un clic

## ⚠️ Avertissements

- **Testez d'abord** avec le mode testnet
- **Commencez petit** avec de faibles montants
- **Pas de conseil financier** - utilisez à vos risques
- **Surveillez les frais** de trading Binance
- **Marché 24/7** - les prix changent constamment

---

**Happy Trading! 🚀₿**

*Tradez de manière responsable et ne risquez que ce que vous pouvez vous permettre de perdre.*