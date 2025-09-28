#!/usr/bin/env python3
"""
Performance Analytics - TWR (Time-Weighted Return) Tracker
Module pour calculer et afficher les vraies performances de trading
"""
import tkinter as tk
import threading
import json
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class PerformanceJSONManager:
    """Gestionnaire JSON pour le tracking de performance"""

    def __init__(self, snapshots_file="snapshots.json", cashflows_file="cashflows.json"):
        self.snapshots_file = snapshots_file
        self.cashflows_file = cashflows_file
        self.ensure_files_exist()


    def ensure_files_exist(self):
        """S'assure que les fichiers JSON existent"""
        if not os.path.exists(self.snapshots_file):
            with open(self.snapshots_file, 'w') as f:
                json.dump([], f)

        if not os.path.exists(self.cashflows_file):
            with open(self.cashflows_file, 'w') as f:
                json.dump([], f)

    def save_snapshot(self, timestamp, total_value, composition):
        """Sauvegarde un snapshot du portfolio"""
        try:
            snapshots = self.load_snapshots()

            # Créer le nouveau snapshot
            new_snapshot = {
                'timestamp': timestamp.isoformat(),
                'total_value_usd': total_value,
                'composition': composition
            }

            snapshots.append(new_snapshot)

            # Trier par timestamp
            snapshots.sort(key=lambda x: x['timestamp'])

            # Sauvegarder
            with open(self.snapshots_file, 'w') as f:
                json.dump(snapshots, f, indent=2)

        except Exception as e:
            logger.error(f"Erreur sauvegarde snapshot: {e}")

    def add_snapshot_manually(self, timestamp, total_value, composition):
        """Ajoute manuellement un snapshot"""
        self.save_snapshot(timestamp, total_value, composition)
        logger.info(f"📸 Snapshot manuel ajouté: ${total_value:.2f} à {timestamp}")

    def load_snapshots(self):
        """Charge tous les snapshots depuis le fichier JSON"""
        try:
            with open(self.snapshots_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement snapshots: {e}")
            return []

    def save_cash_flow(self, timestamp, amount, cf_type, description=""):
        """Sauvegarde un cash flow (dépôt/retrait)"""
        try:
            cash_flows = self.load_cash_flows()

            # Créer le nouveau cash flow
            new_cash_flow = {
                'timestamp': timestamp.isoformat(),
                'amount_usd': amount,
                'type': cf_type,
                'description': description
            }

            cash_flows.append(new_cash_flow)

            # Trier par timestamp
            cash_flows.sort(key=lambda x: x['timestamp'])

            # Sauvegarder
            with open(self.cashflows_file, 'w') as f:
                json.dump(cash_flows, f, indent=2)

        except Exception as e:
            logger.error(f"Erreur sauvegarde cash flow: {e}")

    def load_cash_flows(self):
        """Charge tous les cash flows depuis le fichier JSON"""
        try:
            with open(self.cashflows_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement cash flows: {e}")
            return []

    def get_snapshots(self, start_date=None, end_date=None):
        """Récupère les snapshots dans une période"""
        try:
            snapshots = self.load_snapshots()
            result = []

            for snapshot in snapshots:
                snapshot_date = datetime.fromisoformat(snapshot['timestamp'])

                # Filtrer par date si spécifié
                if start_date and snapshot_date < start_date:
                    continue
                if end_date and snapshot_date > end_date:
                    continue

                result.append({
                    'timestamp': snapshot_date,
                    'total_value': snapshot['total_value_usd'],
                    'composition': snapshot['composition']
                })

            return result
        except Exception as e:
            logger.error(f"Erreur récupération snapshots: {e}")
            return []

    def get_cash_flows(self, start_date=None, end_date=None):
        """Récupère les cash flows dans une période"""
        try:
            cash_flows = self.load_cash_flows()
            result = []

            for cf in cash_flows:
                cf_date = datetime.fromisoformat(cf['timestamp'])

                # Filtrer par date si spécifié
                if start_date and cf_date < start_date:
                    continue
                if end_date and cf_date > end_date:
                    continue

                result.append({
                    'timestamp': cf_date,
                    'amount': cf['amount_usd'],
                    'type': cf['type'],
                    'description': cf['description']
                })

            return result
        except Exception as e:
            logger.error(f"Erreur récupération cash flows: {e}")
            return []


class PerformanceTracker:
    """Calculateur de performance TWR et métriques associées"""

    def __init__(self, trader):
        self.trader = trader
        self.db = PerformanceJSONManager()
        self.last_known_balances = {}

    def detect_cash_flows_eur_usdc(self):
        """Détecte les cash flows EUR->USDC et USDC->EUR"""
        try:
            # Charger les snapshots existants
            snapshots = self.db.get_snapshots()

            if len(snapshots) < 2:
                return

            # Analyser les variations d'USDC entre snapshots
            for i in range(1, len(snapshots)):
                prev_snapshot = snapshots[i-1]
                curr_snapshot = snapshots[i]

                # Extraire les balances USDC
                prev_usdc = prev_snapshot['composition'].get('USDC', {}).get('balance', 0)
                curr_usdc = curr_snapshot['composition'].get('USDC', {}).get('balance', 0)

                usdc_diff = curr_usdc - prev_usdc

                # Seuil significatif pour détecter un cash flow (>50 USDC de variation)
                if abs(usdc_diff) > 50:
                    timestamp = curr_snapshot['timestamp']

                    if usdc_diff > 0:
                        # Augmentation USDC = Dépôt EUR->USDC
                        self.db.save_cash_flow(
                            timestamp, usdc_diff, 'DEPOSIT',
                            f"Dépôt EUR convertis en USDC (+{usdc_diff:.2f})"
                        )
                    else:
                        # Diminution USDC = Retrait USDC->EUR
                        self.db.save_cash_flow(
                            timestamp, usdc_diff, 'WITHDRAW',
                            f"Retrait USDC convertis en EUR ({usdc_diff:.2f})"
                        )

            logger.info("🔍 Détection cash flows EUR<->USDC terminée")

        except Exception as e:
            logger.error(f"Erreur détection cash flows EUR/USDC: {e}")

    def generate_fake_data_for_testing(self):
        """Génère des données factices pour tester le TWR"""
        import random

        logger.info("🔧 Génération de données factices pour test TWR...")

        # Point de départ il y a 10 jours
        start_date = datetime.now() - timedelta(days=10)
        base_value = 10000.0  # Portfolio initial de 10k$

        # Snapshots quotidiens avec évolution réaliste
        current_value = base_value
        for i in range(11):  # 11 snapshots sur 10 jours
            snapshot_date = start_date + timedelta(days=i)

            # Variation quotidienne entre -5% et +8%
            daily_variation = random.uniform(-0.05, 0.08)
            current_value *= (1 + daily_variation)

            # Composition factice (simulate un portfolio crypto)
            composition = {
                'BTC': {
                    'balance': current_value * 0.4 / 45000,  # 40% en BTC
                    'usd_value': current_value * 0.4,
                    'percentage': 40.0
                },
                'ETH': {
                    'balance': current_value * 0.3 / 3000,   # 30% en ETH
                    'usd_value': current_value * 0.3,
                    'percentage': 30.0
                },
                'USDT': {
                    'balance': current_value * 0.3,          # 30% en USDT
                    'usd_value': current_value * 0.3,
                    'percentage': 30.0
                }
            }

            self.db.save_snapshot(snapshot_date, current_value, composition)

        # Cash flows factices
        # Dépôt après 3 jours
        deposit_date = start_date + timedelta(days=3, hours=10)
        self.db.save_cash_flow(deposit_date, 2000.0, 'DEPOSIT', 'Test dépôt USDT')

        # Retrait après 7 jours
        withdraw_date = start_date + timedelta(days=7, hours=14)
        self.db.save_cash_flow(withdraw_date, -1500.0, 'WITHDRAW', 'Test retrait USDT')

        logger.info(f"✅ Données factices générées:")
        logger.info(f"   - 11 snapshots du {start_date.date()} à aujourd'hui")
        logger.info(f"   - 1 dépôt de 2000$ le {deposit_date.date()}")
        logger.info(f"   - 1 retrait de 1500$ le {withdraw_date.date()}")
        logger.info(f"   - Portfolio final: ${current_value:.2f}")

        return True

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
            last_snapshot = snapshots[-1]['timestamp']
            days_tracking = (last_snapshot - first_snapshot).days

            return {
                'days': days_tracking,
                'first_snapshot': first_snapshot,
                'last_snapshot': last_snapshot,
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

            logger.info(f"TWR Debug: période {start_date} à {end_date}")
            logger.info(f"  - Snapshots trouvés: {len(snapshots)}")
            logger.info(f"  - Cash flows trouvés: {len(cash_flows)}")

            if len(snapshots) < 2:
                logger.warning(f"  - Pas assez de snapshots ({len(snapshots)}) pour calculer TWR")
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
            logger.info(f"  - Périodes à calculer: {len(periods)}")

            for i, period in enumerate(periods):
                if period['start_value'] > 0:
                    period_return = (
                        (period['end_value'] - period['start_value'] - period['cash_flow'])
                        / (period['start_value'] + max(0, period['cash_flow']))
                    )
                    cumulative_return *= (1 + period_return)
                    logger.info(f"    Période {i+1}: {period['start_value']:.0f} -> {period['end_value']:.0f} (CF: {period['cash_flow']:.0f}) = {period_return*100:.2f}%")

            twr = cumulative_return - 1
            logger.info(f"  - TWR final: {twr*100:.2f}%")
            return twr

        except Exception as e:
            logger.error(f"Erreur calcul TWR: {e}")
            return None


    def calculate_performance_metrics(self, days):
        """Calcule toutes les métriques pour une période"""
        try:
            # Utiliser la date du dernier snapshot comme référence au lieu de maintenant
            all_snapshots = self.db.get_snapshots()
            if not all_snapshots:
                return None

            end_date = all_snapshots[-1]['timestamp']  # Dernier snapshot
            start_date = end_date - timedelta(days=days)

            # TWR du portfolio
            twr = self.calculate_twr(start_date, end_date)

            return {
                'period_days': days,
                'twr': twr,
                'twr_annualized': ((1 + twr) ** (365 / days) - 1) if twr is not None and days <= 365 else None,
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

        # Variables de statut interne
        self.tracking_status = tk.StringVar(value="Initialisation tracking...")

        # Initialisation sans snapshot immédiat
        self.snapshot_taken_on_launch = False
        self.first_refresh_done = False

    def take_launch_snapshot_if_needed(self):
        """Vérifie au lancement mais attend le premier rafraîchissement pour snapshot"""
        if self.snapshot_taken_on_launch:
            return

        # Marquer comme traité pour éviter les rappels
        self.snapshot_taken_on_launch = True

        # Actualiser l'affichage sans prendre de snapshot
        stats = self.tracker.get_tracking_stats()
        if stats['total_snapshots'] == 0:
            self.tracking_status.set("📊 En attente du premier rafraîchissement...")
        else:
            if stats['days'] == 0:
                self.tracking_status.set("📊 Tracking démarré - En attente rafraîchissement")
            else:
                self.tracking_status.set(f"📊 Données depuis {stats['days']} jours - En attente rafraîchissement")


        # Démarrer les snapshots périodiques toutes les 2h
        self.start_periodic_snapshots()
        logger.info("📸 Snapshot sera pris après le premier rafraîchissement du portfolio")

    def start_periodic_snapshots(self):
        """Démarre les snapshots automatiques toutes les 2h"""
        def periodic_snapshot():
            while True:
                try:
                    # Attendre 2 heures (7200 secondes)
                    threading.Event().wait(7200)

                    # Prendre un snapshot
                    snapshot_taken = self.tracker.save_current_snapshot()
                    if snapshot_taken:
                        logger.info("📸 Snapshot automatique périodique (2h)")

                except Exception as e:
                    logger.error(f"Erreur snapshot périodique: {e}")

        # Démarrer le thread en arrière-plan
        threading.Thread(target=periodic_snapshot, daemon=True).start()
        logger.info("⏰ Snapshots automatiques toutes les 2h activés")

    def check_and_take_snapshot_after_refresh(self):
        """Prend un snapshot après le premier rafraîchissement si nécessaire"""
        try:
            logger.info("📊 Vérification snapshot après premier rafraîchissement...")
            snapshots = self.tracker.db.get_snapshots()

            if not snapshots:
                # Premier snapshot jamais pris
                logger.info("📸 Aucun snapshot existant - prise du premier snapshot")
                snapshot_taken = self.tracker.save_current_snapshot()
                if snapshot_taken:
                    logger.info("✅ Premier snapshot sauvé avec succès")
                    self.tracking_status.set("📊 Tracking démarré")
                return

            # Vérifier si le dernier snapshot a plus de 2h
            last_snapshot_time = snapshots[-1]['timestamp']
            now = datetime.now()
            hours_since_last = (now - last_snapshot_time).total_seconds() / 3600

            if (now - last_snapshot_time).total_seconds() > 7200:  # 2h en secondes
                logger.info(f"📸 Dernier snapshot date de {hours_since_last:.1f}h - Snapshot de rattrapage nécessaire")
                snapshot_taken = self.tracker.save_current_snapshot()
                if snapshot_taken:
                    logger.info("✅ Snapshot de rattrapage sauvé avec succès")
                    # Actualiser le statut
                    stats = self.tracker.get_tracking_stats()
                    self.tracking_status.set(f"📊 Données depuis {stats['days']} jours")
            else:
                logger.info(f"📊 Dernier snapshot date de {hours_since_last:.1f}h - Pas de snapshot nécessaire")
                # Actualiser juste le statut
                stats = self.tracker.get_tracking_stats()
                self.tracking_status.set(f"📊 Données depuis {stats['days']} jours")

        except Exception as e:
            logger.error(f"Erreur snapshot après rafraîchissement: {e}")



    def refresh_metrics(self):
        """Met à jour le statut de tracking"""
        try:
            stats = self.tracker.get_tracking_stats()
            days_available = stats['days']

            if days_available == 0:
                self.tracking_status.set("📊 Tracking démarré aujourd'hui")
            else:
                self.tracking_status.set(f"📊 Données depuis {days_available} jours")

            logger.info(f"Métriques de performance actualisées pour {days_available} jours de données")

        except Exception as e:
            logger.error(f"Erreur refresh métriques: {e}")





