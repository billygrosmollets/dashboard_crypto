#!/usr/bin/env python3
"""
Performance Analytics - TWR (Time-Weighted Return) Tracker
Module pour calculer et afficher les vraies performances de trading
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sqlite3
import json
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class PerformanceDatabase:
    """Gestionnaire de base de données pour le tracking de performance"""

    def __init__(self, db_path="performance.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialise la base de données SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        total_value_usd REAL NOT NULL,
                        composition TEXT NOT NULL,
                        source TEXT DEFAULT 'auto'
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cash_flows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        amount_usd REAL NOT NULL,
                        type TEXT NOT NULL,
                        description TEXT,
                        auto_detected BOOLEAN DEFAULT 1
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_periods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        twr REAL NOT NULL,
                        benchmark_btc REAL,
                        benchmark_eth REAL,
                        alpha_btc REAL,
                        alpha_eth REAL
                    )
                """)

                conn.commit()
                logger.info("Base de données performance initialisée")
        except Exception as e:
            logger.error(f"Erreur initialisation DB: {e}")

    def save_snapshot(self, timestamp, total_value, composition):
        """Sauvegarde un snapshot du portfolio"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO portfolio_snapshots
                    (timestamp, total_value_usd, composition)
                    VALUES (?, ?, ?)
                """, (timestamp.isoformat(), total_value, json.dumps(composition)))
                conn.commit()
        except Exception as e:
            logger.error(f"Erreur sauvegarde snapshot: {e}")

    def save_cash_flow(self, timestamp, amount, cf_type, description=""):
        """Sauvegarde un cash flow (dépôt/retrait)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO cash_flows
                    (timestamp, amount_usd, type, description)
                    VALUES (?, ?, ?, ?)
                """, (timestamp.isoformat(), amount, cf_type, description))
                conn.commit()
        except Exception as e:
            logger.error(f"Erreur sauvegarde cash flow: {e}")

    def get_snapshots(self, start_date=None, end_date=None):
        """Récupère les snapshots dans une période"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT timestamp, total_value_usd, composition FROM portfolio_snapshots"
                params = []

                if start_date or end_date:
                    conditions = []
                    if start_date:
                        conditions.append("timestamp >= ?")
                        params.append(start_date.isoformat())
                    if end_date:
                        conditions.append("timestamp <= ?")
                        params.append(end_date.isoformat())
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY timestamp"

                cursor = conn.execute(query, params)
                return [{
                    'timestamp': datetime.fromisoformat(row[0]),
                    'total_value': row[1],
                    'composition': json.loads(row[2])
                } for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erreur récupération snapshots: {e}")
            return []

    def get_cash_flows(self, start_date=None, end_date=None):
        """Récupère les cash flows dans une période"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT timestamp, amount_usd, type, description FROM cash_flows"
                params = []

                if start_date or end_date:
                    conditions = []
                    if start_date:
                        conditions.append("timestamp >= ?")
                        params.append(start_date.isoformat())
                    if end_date:
                        conditions.append("timestamp <= ?")
                        params.append(end_date.isoformat())
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY timestamp"

                cursor = conn.execute(query, params)
                return [{
                    'timestamp': datetime.fromisoformat(row[0]),
                    'amount': row[1],
                    'type': row[2],
                    'description': row[3]
                } for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erreur récupération cash flows: {e}")
            return []


class PerformanceTracker:
    """Calculateur de performance TWR et métriques associées"""

    def __init__(self, trader):
        self.trader = trader
        self.db = PerformanceDatabase()
        self.last_known_balances = {}

    def detect_cash_flows(self, days=30):
        """Détecte automatiquement les cash flows via l'API Binance"""
        try:
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            # Détecter les dépôts
            deposits = self.trader.client.get_deposit_history(startTime=start_time)
            for deposit in deposits:
                if deposit['status'] == 1:  # Réussi
                    timestamp = datetime.fromtimestamp(deposit['insertTime'] / 1000)
                    amount = float(deposit['amount'])

                    # Convertir en USD si possible
                    if deposit['coin'] in ['USDT', 'USDC', 'BUSD']:
                        amount_usd = amount
                    else:
                        # Approximation via prix actuel (à améliorer)
                        amount_usd = amount * self._get_asset_price_usd(deposit['coin'])

                    self.db.save_cash_flow(
                        timestamp, amount_usd, 'DEPOSIT',
                        f"Dépôt {deposit['coin']}"
                    )

            # Détecter les retraits
            withdraws = self.trader.client.get_withdraw_history(startTime=start_time)
            for withdraw in withdraws:
                if withdraw['status'] == 6:  # Réussi
                    timestamp = datetime.fromtimestamp(withdraw['applyTime'] / 1000)
                    amount = float(withdraw['amount'])

                    # Convertir en USD si possible
                    if withdraw['coin'] in ['USDT', 'USDC', 'BUSD']:
                        amount_usd = amount
                    else:
                        amount_usd = amount * self._get_asset_price_usd(withdraw['coin'])

                    self.db.save_cash_flow(
                        timestamp, -amount_usd, 'WITHDRAW',
                        f"Retrait {withdraw['coin']}"
                    )

        except Exception as e:
            logger.error(f"Erreur détection cash flows: {e}")

    def _get_asset_price_usd(self, asset):
        """Obtient le prix USD d'un actif"""
        try:
            if asset in ['USDT', 'USDC', 'BUSD']:
                return 1.0

            for quote in ['USDT', 'USDC']:
                symbol = f"{asset}{quote}"
                if symbol in self.trader.all_symbols:
                    ticker = self.trader.client.get_symbol_ticker(symbol=symbol)
                    return float(ticker['price'])

            return 0.0
        except:
            return 0.0

    def save_current_snapshot(self):
        """Sauvegarde un snapshot du portfolio actuel"""
        try:
            balances = self.trader.get_all_balances_usd(1.0)  # Minimum 1$ pour inclure plus d'actifs
            total_value = sum(b['usd_value'] for b in balances.values())

            if total_value == 0:
                logger.warning("Portfolio vide, snapshot ignoré")
                return False

            # Simplifier la composition pour stockage
            composition = {}
            for asset, data in balances.items():
                if data['usd_value'] > 1.0:  # Garder seulement les positions significatives
                    composition[asset] = {
                        'balance': data['balance'],
                        'usd_value': data['usd_value'],
                        'percentage': (data['usd_value'] / total_value * 100) if total_value > 0 else 0
                    }

            self.db.save_snapshot(datetime.now(), total_value, composition)
            self.last_known_balances = balances

            logger.info(f"📸 Snapshot sauvé: ${total_value:.2f} total")
            return True

        except Exception as e:
            logger.error(f"Erreur sauvegarde snapshot: {e}")
            return False

    def get_tracking_stats(self):
        """Retourne les statistiques du tracking (nombre de jours, etc.)"""
        try:
            snapshots = self.db.get_snapshots()
            if not snapshots:
                return {'days': 0, 'first_snapshot': None, 'total_snapshots': 0}

            first_snapshot = snapshots[0]['timestamp']
            days_tracking = (datetime.now() - first_snapshot).days

            return {
                'days': days_tracking,
                'first_snapshot': first_snapshot,
                'total_snapshots': len(snapshots)
            }

        except Exception as e:
            logger.error(f"Erreur stats tracking: {e}")
            return {'days': 0, 'first_snapshot': None, 'total_snapshots': 0}

    def calculate_twr(self, start_date, end_date):
        """Calcule le TWR pour une période donnée"""
        try:
            snapshots = self.db.get_snapshots(start_date, end_date)
            cash_flows = self.db.get_cash_flows(start_date, end_date)

            if len(snapshots) < 2:
                return None

            # Créer les périodes basées sur les cash flows
            periods = []
            period_start = snapshots[0]

            # Trier tous les événements par timestamp
            all_events = []
            for snapshot in snapshots[1:]:
                all_events.append(('snapshot', snapshot))
            for cf in cash_flows:
                all_events.append(('cash_flow', cf))

            all_events.sort(key=lambda x: x[1]['timestamp'])

            # Créer des périodes
            current_start = period_start
            cumulative_cf = 0

            for event_type, event_data in all_events:
                if event_type == 'cash_flow':
                    cumulative_cf += event_data['amount']
                elif event_type == 'snapshot':
                    # Fin de période
                    periods.append({
                        'start_value': current_start['total_value'],
                        'end_value': event_data['total_value'],
                        'cash_flow': cumulative_cf,
                        'start_time': current_start['timestamp'],
                        'end_time': event_data['timestamp']
                    })

                    # Nouvelle période
                    current_start = event_data
                    cumulative_cf = 0

            # Calculer TWR
            cumulative_return = 1.0

            for period in periods:
                if period['start_value'] > 0:
                    period_return = (
                        (period['end_value'] - period['start_value'] - period['cash_flow'])
                        / (period['start_value'] + max(0, period['cash_flow']))
                    )
                    cumulative_return *= (1 + period_return)

            twr = cumulative_return - 1
            return twr

        except Exception as e:
            logger.error(f"Erreur calcul TWR: {e}")
            return None

    def get_benchmark_performance(self, asset, start_date, end_date):
        """Calcule la performance d'un benchmark (BTC, ETH) sur la période"""
        try:
            # Obtenir prix de début et fin de période
            start_price = self._get_historical_price(asset, start_date)
            end_price = self._get_historical_price(asset, end_date)

            if start_price > 0 and end_price > 0:
                return (end_price / start_price) - 1
            return 0.0

        except Exception as e:
            logger.error(f"Erreur benchmark {asset}: {e}")
            return 0.0

    def _get_historical_price(self, asset, date):
        """Obtient le prix historique d'un actif"""
        try:
            symbol = f"{asset}USDT"
            start_time = int(date.timestamp() * 1000)
            end_time = start_time + (24 * 60 * 60 * 1000)

            klines = self.trader.client.get_klines(
                symbol=symbol,
                interval='1d',
                startTime=start_time,
                endTime=end_time,
                limit=1
            )

            if klines:
                return float(klines[0][4])  # Prix de clôture
            else:
                # Fallback sur prix actuel si pas d'historique
                ticker = self.trader.client.get_symbol_ticker(symbol=symbol)
                return float(ticker['price'])

        except Exception as e:
            logger.error(f"Erreur prix historique {asset}: {e}")
            return 0.0

    def calculate_performance_metrics(self, days):
        """Calcule toutes les métriques pour une période"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # TWR du portfolio
            twr = self.calculate_twr(start_date, end_date)

            # Benchmarks
            btc_performance = self.get_benchmark_performance('BTC', start_date, end_date)
            eth_performance = self.get_benchmark_performance('ETH', start_date, end_date)

            # Alpha (outperformance)
            alpha_btc = twr - btc_performance if twr is not None else None
            alpha_eth = twr - eth_performance if twr is not None else None

            return {
                'period_days': days,
                'twr': twr,
                'twr_annualized': ((1 + twr) ** (365 / days) - 1) if twr is not None else None,
                'benchmark_btc': btc_performance,
                'benchmark_eth': eth_performance,
                'alpha_btc': alpha_btc,
                'alpha_eth': alpha_eth,
                'start_date': start_date,
                'end_date': end_date
            }

        except Exception as e:
            logger.error(f"Erreur calcul métriques {days}j: {e}")
            return None


class PerformanceInterface:
    """Interface utilisateur pour les analytics de performance"""

    def __init__(self, trader):
        self.trader = trader
        self.tracker = PerformanceTracker(trader)

        # Variables d'affichage
        self.metrics_7d = tk.StringVar(value="7j: Initialisation...")
        self.metrics_30d = tk.StringVar(value="30j: Initialisation...")
        self.metrics_90d = tk.StringVar(value="90j: Initialisation...")

        self.benchmark_btc = tk.StringVar(value="vs BTC: --")
        self.benchmark_eth = tk.StringVar(value="vs ETH: --")
        self.tracking_status = tk.StringVar(value="Initialisation tracking...")

        # Initialisation sans snapshot immédiat
        self.snapshot_taken_on_launch = False

    def take_launch_snapshot_if_needed(self):
        """Prend un snapshot au lancement si pas encore fait et portfolio chargé"""
        if self.snapshot_taken_on_launch:
            return

        def take_snapshot():
            try:
                # Prendre snapshot automatique
                snapshot_taken = self.tracker.save_current_snapshot()

                if snapshot_taken:
                    self.snapshot_taken_on_launch = True
                    # Obtenir stats de tracking
                    stats = self.tracker.get_tracking_stats()

                    if stats['days'] == 0:
                        self.tracking_status.set("📊 Tracking démarré au lancement")
                    else:
                        self.tracking_status.set(f"📊 Données depuis {stats['days']} jours")

                    # Actualiser l'affichage adaptatif
                    self.update_adaptive_display(stats)
                    logger.info("🚀 Snapshot de lancement pris avec succès")

            except Exception as e:
                logger.error(f"Erreur snapshot lancement: {e}")
                self.tracking_status.set("❌ Erreur snapshot")

        threading.Thread(target=take_snapshot, daemon=True).start()

    def update_adaptive_display(self, stats):
        """Met à jour l'affichage selon les données disponibles"""
        days = stats['days']

        if days < 7:
            self.metrics_7d.set("7j: Attendez 7 jours")
            self.metrics_30d.set("30j: Attendez 30 jours")
            self.metrics_90d.set("90j: Attendez 90 jours")
        elif days < 30:
            self.metrics_7d.set("7j: Données disponibles")
            self.metrics_30d.set("30j: Attendez 30 jours")
            self.metrics_90d.set("90j: Attendez 90 jours")
        elif days < 90:
            self.metrics_7d.set("7j: Données disponibles")
            self.metrics_30d.set("30j: Données disponibles")
            self.metrics_90d.set("90j: Attendez 90 jours")
        else:
            self.metrics_7d.set("7j: Données disponibles")
            self.metrics_30d.set("30j: Données disponibles")
            self.metrics_90d.set("90j: Données disponibles")

    def create_performance_ui(self, parent):
        """Crée l'interface Performance Analytics"""
        perf_frame = ttk.LabelFrame(parent, text="📊 Performance Analytics (TWR)", padding="10")
        perf_frame.pack(fill=tk.X, padx=10, pady=5)

        # Ligne 0 - Status tracking
        status_row = ttk.Frame(perf_frame)
        status_row.pack(fill=tk.X, pady=2)
        ttk.Label(status_row, textvariable=self.tracking_status, font=("Arial", 9), foreground="gray").pack(side=tk.LEFT)

        # Ligne 1 - Métriques principales
        metrics_row = ttk.Frame(perf_frame)
        metrics_row.pack(fill=tk.X, pady=2)

        ttk.Label(metrics_row, textvariable=self.metrics_7d, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        ttk.Label(metrics_row, textvariable=self.metrics_30d, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        ttk.Label(metrics_row, textvariable=self.metrics_90d, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)

        # Ligne 2 - Benchmarks
        benchmark_row = ttk.Frame(perf_frame)
        benchmark_row.pack(fill=tk.X, pady=2)

        ttk.Label(benchmark_row, textvariable=self.benchmark_btc, font=("Arial", 9), foreground="blue").pack(side=tk.LEFT, padx=10)
        ttk.Label(benchmark_row, textvariable=self.benchmark_eth, font=("Arial", 9), foreground="purple").pack(side=tk.LEFT, padx=10)

        # Ligne 3 - Boutons
        buttons_row = ttk.Frame(perf_frame)
        buttons_row.pack(fill=tk.X, pady=5)

        ttk.Button(buttons_row, text="🔄 Actualiser", command=self.refresh_metrics).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_row, text="🔍 Analyser", command=self.detailed_analysis).pack(side=tk.LEFT, padx=5)

        return perf_frame

    def refresh_metrics(self):
        """Actualise toutes les métriques de performance"""
        def calculate():
            try:
                # Obtenir stats de tracking d'abord
                stats = self.tracker.get_tracking_stats()
                days_available = stats['days']

                # Mettre à jour le status
                if days_available == 0:
                    self.tracking_status.set("📊 Tracking démarré aujourd'hui")
                else:
                    self.tracking_status.set(f"📊 Données depuis {days_available} jours")

                # Calculer les métriques selon disponibilité
                periods_to_calculate = []
                if days_available >= 7:
                    periods_to_calculate.append((7, self.metrics_7d))
                if days_available >= 30:
                    periods_to_calculate.append((30, self.metrics_30d))
                if days_available >= 90:
                    periods_to_calculate.append((90, self.metrics_90d))

                # Calculer les métriques disponibles
                for days, var in periods_to_calculate:
                    var.set(f"{days}j: Calcul...")

                    metrics = self.tracker.calculate_performance_metrics(days)

                    if metrics and metrics['twr'] is not None:
                        twr = metrics['twr'] * 100
                        emoji = "📈" if twr > 0 else "📉" if twr < 0 else "➡️"
                        var.set(f"{days}j: {emoji} {twr:+.1f}%")
                    else:
                        var.set(f"{days}j: ❌ N/A")

                # Calculer benchmarks pour 30j si disponible
                if days_available >= 30:
                    metrics_30 = self.tracker.calculate_performance_metrics(30)
                    if metrics_30:
                        btc_perf = metrics_30['benchmark_btc'] * 100
                        eth_perf = metrics_30['benchmark_eth'] * 100

                        alpha_btc = metrics_30['alpha_btc'] * 100 if metrics_30['alpha_btc'] else 0
                        alpha_eth = metrics_30['alpha_eth'] * 100 if metrics_30['alpha_eth'] else 0

                        self.benchmark_btc.set(f"vs BTC: {btc_perf:+.1f}% (α: {alpha_btc:+.1f}%)")
                        self.benchmark_eth.set(f"vs ETH: {eth_perf:+.1f}% (α: {alpha_eth:+.1f}%)")
                else:
                    self.benchmark_btc.set("vs BTC: Attendez 30 jours")
                    self.benchmark_eth.set("vs ETH: Attendez 30 jours")

                # Mettre à jour l'affichage adaptatif
                self.update_adaptive_display(stats)

            except Exception as e:
                logger.error(f"Erreur refresh métriques: {e}")
                messagebox.showerror("Erreur", f"Erreur calcul: {e}")

        threading.Thread(target=calculate, daemon=True).start()

    def detailed_analysis(self):
        """Affiche une analyse détaillée"""
        def analyze():
            try:
                # Créer une fenêtre popup avec plus de détails
                analysis_window = tk.Toplevel()
                analysis_window.title("📊 Analyse Détaillée")
                analysis_window.geometry("600x400")

                # TODO: Implémenter analyse détaillée avec graphiques
                text_area = tk.Text(analysis_window, wrap=tk.WORD, padx=10, pady=10)
                text_area.pack(fill=tk.BOTH, expand=True)

                # Placeholder pour analyse détaillée
                analysis_text = """
Performance Analytics - Analyse Détaillée

🎯 Time-Weighted Return (TWR)
Mesure la performance pure de vos décisions de trading,
indépendamment du timing et de la taille de vos investissements.

📈 Métriques Calculées:
- TWR 7/30/90 jours
- Performance vs Hold BTC/ETH
- Alpha (outperformance vs benchmarks)

💡 Prochaines fonctionnalités:
- Graphiques de performance
- Attribution par actif
- Analyse des drawdowns
- Sharpe Ratio

Base de données: performance.db
Snapshots automatiques quotidiens
Détection auto des cash flows
"""

                text_area.insert(tk.END, analysis_text)
                text_area.config(state=tk.DISABLED)

            except Exception as e:
                logger.error(f"Erreur analyse détaillée: {e}")

        threading.Thread(target=analyze, daemon=True).start()