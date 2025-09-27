# 🚀 Binance Advanced Trading Platform

Une application Python GUI complète pour le trading multi-actifs avec gestion automatique de portefeuille sur Binance.

## ✨ Fonctionnalités

### 🔑 Connexion Sécurisée
- Configuration simple via fichier `.env`
- Support mode testnet pour tests sans risque
- Chargement automatique des clés API

### 💰 Gestion Multi-Actifs
- Affichage de tous les actifs > 5$ USD
- Calcul automatique des valeurs en USD
- Pourcentage de répartition du portfolio
- Distinction fonds libres/bloqués

### ⚡ Trading Intelligent
- **Conversion multi-actifs** : N'importe quel actif vers un autre
- **Routes intelligentes** :
  - Conversion directe si paire disponible
  - Conversion inverse automatique
  - Conversion triangulaire via USDT
- **Boutons rapides** : 25%, 50%, 75%, 100%

### 📊 Gestion de Portfolio Automatique
- **Répartition personnalisée** : % BTC, % USDC, % Altcoins
- **Profils de risque** :
  - 🛡️ **Conservateur** : 15% BTC, 60% USDC, 25% Altcoins
  - ⚖️ **Modéré** : 25% BTC, 40% USDC, 35% Altcoins
  - 🚀 **Agressif** : 30% BTC, 20% USDC, 50% Altcoins
- **Simulation** avant exécution
- **Répartition équilibrée** automatique des altcoins

### 📋 Historique Complet
- Transactions multi-paires
- Détails : date, type, quantité, prix, commissions

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
# Éditer le fichier .env
BINANCE_API_KEY=votre_cle_api_ici
BINANCE_API_SECRET=votre_secret_ici
BINANCE_TESTNET=true
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

### Trading de Base
1. **Onglet Balances** → Voir votre portfolio
2. **Onglet Trading** → Convertir vos actifs
3. Sélectionner actif source/destination
4. Choisir montant ou utiliser les %
5. Confirmer la conversion

### Gestion de Portfolio
1. **Onglet Portfolio** → Définir vos objectifs
2. **Choisir un profil** ou personnaliser les %
3. **"Calculer"** → Voir la répartition actuelle vs cible
4. **"Simuler"** → Prévisualiser les actions nécessaires
5. **Analyser** le plan avant exécution

### Exemple de Rééquilibrage

**Situation :**
- Portfolio : $10,000
- Actuel : 10% BTC, 50% USDC, 40% ETH
- Objectif "Modéré" : 25% BTC, 40% USDC, 35% altcoins

**Actions automatiques :**
- Acheter $1,500 de BTC (10% → 25%)
- Vendre $1,000 de USDC (50% → 40%)
- Vendre $500 d'ETH (répartition équilibrée altcoins)

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
├── main.py           # Application complète (GUI + logique)
├── .env              # Configuration API (à éditer)
├── requirements.txt  # Dépendances Python
├── README.md         # Documentation
└── .gitignore        # Fichiers à ignorer
```

## 🔧 Développement

### Architecture
- **EnvLoader** : Chargement des variables d'environnement
- **BinanceTrader** : API Binance + conversions intelligentes
- **PortfolioManager** : Logique de rééquilibrage
- **AdvancedTradingApp** : Interface GUI avec onglets

### Fonctionnalités Avancées
- **Conversion triangulaire** automatique via USDT
- **Calcul intelligent** des routes de trading
- **Formatage précis** des quantités selon Binance
- **Gestion d'erreurs** robuste
- **Threading** pour UI réactive

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