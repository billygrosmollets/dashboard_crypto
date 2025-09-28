#!/usr/bin/env python3
"""
Binance Trading Platform - Portfolio Main Interface
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timedelta
import os
import logging
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Imports des modules refactorisés
from config_converter import PortfolioConfig
from performance_tracker import PerformanceInterface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CLASSES UTILITAIRES COMPACTES
# ============================================================================

class EnvLoader:
    @staticmethod
    def load_env():
        env_vars = {}
        if not os.path.exists('.env'):
            return env_vars
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"').strip("'")
        except Exception as e:
            logger.error(f"Erreur .env: {e}")
        return env_vars

class BinanceTrader:
    def __init__(self, api_key, api_secret, testnet=False):
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.all_symbols = []
        self.all_assets = set()
        self.exchange_info = None
        logger.info(f"Client Binance initialisé (testnet: {testnet})")
        self._load_exchange_info()

    def _load_exchange_info(self):
        try:
            self.exchange_info = self.client.get_exchange_info()
            self.all_symbols = [s['symbol'] for s in self.exchange_info['symbols'] if s['status'] == 'TRADING']
            for symbol_info in self.exchange_info['symbols']:
                if symbol_info['status'] == 'TRADING':
                    self.all_assets.add(symbol_info['baseAsset'])
                    self.all_assets.add(symbol_info['quoteAsset'])
            logger.info(f"Chargé {len(self.all_symbols)} paires et {len(self.all_assets)} actifs")
        except Exception as e:
            logger.error(f"Erreur chargement exchange info: {e}")

    def get_all_tradeable_assets(self):
        return sorted(list(self.all_assets))

    def get_conversion_path(self, from_asset, to_asset):
        if from_asset == to_asset:
            return None

        direct = f"{from_asset}{to_asset}"
        reverse = f"{to_asset}{from_asset}"

        if direct in self.all_symbols:
            return {'path': 'direct', 'symbol': direct, 'side': 'SELL'}
        elif reverse in self.all_symbols:
            return {'path': 'direct', 'symbol': reverse, 'side': 'BUY'}
        else:
            # Chercher un chemin via USDT, BUSD, BTC
            for intermediate in ['USDT', 'BUSD', 'BTC']:
                if (f"{from_asset}{intermediate}" in self.all_symbols and
                    f"{to_asset}{intermediate}" in self.all_symbols):
                    return {
                        'path': 'triangular',
                        'intermediate': intermediate,
                        'step1': f"{from_asset}{intermediate}",
                        'step2': f"{to_asset}{intermediate}"
                    }
        return None

    def get_conversion_rate(self, from_asset, to_asset, amount=1.0):
        try:
            if from_asset == to_asset:
                return amount

            path = self.get_conversion_path(from_asset, to_asset)
            if not path:
                return None

            if path['path'] == 'direct':
                ticker = self.client.get_symbol_ticker(symbol=path['symbol'])
                price = float(ticker['price'])
                if path['side'] == 'SELL':
                    return amount * price
                else:
                    return amount / price

            elif path['path'] == 'triangular':
                # Conversion via actif intermédiaire
                ticker1 = self.client.get_symbol_ticker(symbol=path['step1'])
                ticker2 = self.client.get_symbol_ticker(symbol=path['step2'])

                intermediate_amount = amount * float(ticker1['price'])
                final_amount = intermediate_amount / float(ticker2['price'])
                return final_amount

        except Exception as e:
            logger.error(f"Erreur calcul taux conversion {from_asset}->{to_asset}: {e}")
            return None

    def test_connection(self):
        try:
            self.client.get_account()
            return True
        except Exception as e:
            logger.error(f"Erreur connexion: {e}")
            return False

    def get_all_balances_usd(self, min_value=300.0):
        account = self.client.get_account()
        tickers = {t['symbol']: float(t['price']) for t in self.client.get_all_tickers()}
        balances = {}
        
        for bal in account['balances']:
            asset, total = bal['asset'], float(bal['free']) + float(bal['locked'])
            if total <= 0:
                continue
                
            if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
                usd_val = total
            else:
                usd_val = 0
                for quote in ['USDT', 'USDC', 'BUSD']:
                    if f"{asset}{quote}" in tickers:
                        usd_val = total * tickers[f"{asset}{quote}"]
                        break
                        
            if usd_val >= min_value:
                balances[asset] = {
                    'balance': total, 'usd_value': usd_val, 
                    'free': float(bal['free']), 'locked': float(bal['locked'])
                }
        return balances

    def format_quantity(self, symbol, quantity):
        try:
            info = self.client.get_symbol_info(symbol)
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step = float(f['stepSize'])
                    precision = len(f"{step:.10f}".rstrip('0').split('.')[1]) if step < 1 else 0
                    return f"{round(quantity / step) * step:.{precision}f}".rstrip('0').rstrip('.')
        except Exception as e:
            logger.error(f"Erreur formatage: {e}")
        return f"{quantity:.8f}"

    def calculate_order_fees(self, order_result):
        """Calcule les frais totaux d'un ordre et retourne les détails"""
        if not isinstance(order_result, dict) or 'fills' not in order_result:
            return {'total_fees': {}, 'fee_details': []}

        total_fees = {}
        fee_details = []

        for fill in order_result['fills']:
            fee_amount = float(fill['commission'])
            fee_asset = fill['commissionAsset']

            # Accumuler les frais par actif
            total_fees[fee_asset] = total_fees.get(fee_asset, 0) + fee_amount

            # Détails pour logging
            fee_details.append({
                'amount': fee_amount,
                'asset': fee_asset,
                'price': float(fill['price']),
                'qty': float(fill['qty'])
            })

        return {'total_fees': total_fees, 'fee_details': fee_details}

    def convert_usdt_value(self, amount, asset):
        """Convertit un montant dans un actif donné vers sa valeur en USDT"""
        if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
            return amount

        try:
            # Essayer de trouver une paire directe avec USDT
            if f"{asset}USDT" in self.all_symbols:
                ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                return amount * float(ticker['price'])
            elif f"USDT{asset}" in self.all_symbols:
                ticker = self.client.get_symbol_ticker(symbol=f"USDT{asset}")
                return amount / float(ticker['price'])
        except Exception as e:
            logger.error(f"Erreur conversion {asset} vers USDT: {e}")

        return 0

    def convert_asset(self, from_asset, to_asset, amount):
        try:
            if from_asset == to_asset:
                logger.warning(f"Conversion inutile: {from_asset} -> {to_asset}")
                return None

            path = self.get_conversion_path(from_asset, to_asset)
            if not path:
                logger.error(f"Aucun chemin de conversion trouvé: {from_asset} -> {to_asset}")
                return None

            if path['path'] == 'direct':
                symbol = path['symbol']
                side = path['side']

                if side == 'SELL':
                    qty = self.format_quantity(symbol, amount)
                    order = self.client.order_market_sell(symbol=symbol, quantity=qty)
                else:
                    # Pour les achats, utiliser directement le montant comme quoteOrderQty
                    # car nous voulons acheter pour X USDC de l'actif de base
                    order = self.client.order_market_buy(symbol=symbol, quoteOrderQty=round(amount, 2))

                # Calculer les frais pour cet ordre
                fee_info = self.calculate_order_fees(order)

                # Calculer la valeur USDT des frais
                total_fee_usdt = 0
                for fee_asset, fee_amount in fee_info['total_fees'].items():
                    fee_usdt = self.convert_usdt_value(fee_amount, fee_asset)
                    total_fee_usdt += fee_usdt

                # Retourner l'ordre avec les informations de frais
                return {
                    'type': 'direct',
                    'order': order,
                    'fees': fee_info,
                    'total_fee_usdt': total_fee_usdt,
                    'symbol': symbol,
                    'side': side
                }

            elif path['path'] == 'triangular':
                # Conversion en deux étapes via actif intermédiaire
                intermediate = path['intermediate']
                step1_symbol = path['step1']  # from_asset -> intermediate
                step2_symbol = path['step2']  # to_asset -> intermediate

                # Étape 1: Convertir from_asset vers intermediate
                qty1 = self.format_quantity(step1_symbol, amount)
                order1 = self.client.order_market_sell(symbol=step1_symbol, quantity=qty1)

                # Calculer la quantité reçue d'actif intermédiaire
                intermediate_received = sum(float(f['qty']) * float(f['price']) for f in order1['fills'])

                # Petit délai pour éviter les erreurs de rate limiting
                time.sleep(0.2)

                # Étape 2: Convertir intermediate vers to_asset
                # Utiliser quoteOrderQty pour acheter to_asset avec l'intermediate
                order2 = self.client.order_market_buy(
                    symbol=step2_symbol,
                    quoteOrderQty=round(intermediate_received * 0.999, 2)  # 0.1% de marge pour les frais
                )

                # Calculer les frais totaux
                fee_info1 = self.calculate_order_fees(order1)
                fee_info2 = self.calculate_order_fees(order2)

                # Combiner les frais des deux ordres
                combined_fees = {}
                for fee_asset, amount in fee_info1['total_fees'].items():
                    combined_fees[fee_asset] = combined_fees.get(fee_asset, 0) + amount
                for fee_asset, amount in fee_info2['total_fees'].items():
                    combined_fees[fee_asset] = combined_fees.get(fee_asset, 0) + amount

                # Calculer la valeur USDT totale des frais
                total_fee_usdt = 0
                for fee_asset, fee_amount in combined_fees.items():
                    fee_usdt = self.convert_usdt_value(fee_amount, fee_asset)
                    total_fee_usdt += fee_usdt

                return {
                    'type': 'triangular',
                    'order1': order1,
                    'order2': order2,
                    'intermediate': intermediate,
                    'intermediate_amount': intermediate_received,
                    'fees1': fee_info1,
                    'fees2': fee_info2,
                    'combined_fees': combined_fees,
                    'total_fee_usdt': total_fee_usdt
                }

        except BinanceAPIException as e:
            if e.code == -2010:
                logger.warning(f"Symbole non permis pour ce compte: {from_asset}->{to_asset} (paire: {path.get('symbol', 'unknown') if path else 'none'})")
                logger.info("Cette erreur peut indiquer un problème de paramètres d'ordre. Vérifiez que la paire est autorisée.")
            else:
                logger.error(f"Erreur API Binance ({e.code}): {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur conversion {from_asset}->{to_asset}: {e}")
            return None

class PortfolioManager:
    def __init__(self, trader):
        self.trader = trader

    def calculate_rebalancing_plan(self, balances, target_alloc):
        total_val = sum(d['usd_value'] for d in balances.values())
        if total_val == 0:
            return {"error": "Portfolio vide"}

        btc_target = total_val * target_alloc['btc_percent'] / 100
        usdc_target = total_val * target_alloc['usdc_percent'] / 100
        alt_target = total_val * target_alloc['altcoin_percent'] / 100
        
        stablecoins = {'USDC', 'USDT', 'BUSD', 'FDUSD', 'DAI'}
        altcoins = {k: v for k, v in balances.items() if k not in stablecoins | {'BTC'}}
        alt_count = len(altcoins) if altcoins else 1
        alt_individual_target = alt_target / alt_count

        plan = {'total_value': total_val, 'actions': []}
        
        # Analyser BTC
        btc_current = balances.get('BTC', {}).get('usd_value', 0)
        btc_diff = btc_target - btc_current
        if abs(btc_diff) > total_val * 0.01:
            plan['actions'].append({
                'asset': 'BTC', 'action': 'ACHETER' if btc_diff > 0 else 'VENDRE',
                'usd_amount': abs(btc_diff), 'priority': 1
            })

        # Analyser USDC
        usdc_current = balances.get('USDC', {}).get('usd_value', 0)
        usdc_diff = usdc_target - usdc_current
        if abs(usdc_diff) > total_val * 0.01:
            plan['actions'].append({
                'asset': 'USDC', 'action': 'ACHETER' if usdc_diff > 0 else 'VENDRE',
                'usd_amount': abs(usdc_diff), 'priority': 1
            })

        # Analyser altcoins
        for asset, data in altcoins.items():
            diff = alt_individual_target - data['usd_value']
            if abs(diff) > total_val * 0.005:
                plan['actions'].append({
                    'asset': asset, 'action': 'ACHETER' if diff > 0 else 'VENDRE',
                    'usd_amount': abs(diff), 'priority': 2
                })

        plan['actions'].sort(key=lambda x: (x['priority'], -x['usd_amount']))
        return plan


# ============================================================================
# APPLICATION PRINCIPALE COMPACTE
# ============================================================================

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Binance Portfolio Manager")
        self.root.geometry("950x800")

        # Variables principales
        self.trader = None
        self.portfolio_manager = None
        self.all_balances = {}

        # Modules refactorisés
        self.portfolio_config = None
        self.crypto_converter = None
        self.performance_interface = None

        self.setup_ui()
        self.load_config()
        self.start_auto_refresh()

    def setup_ui(self):
        # Header avec statut
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header, text="🚀 Binance Portfolio Manager", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="❌ Déconnecté")
        ttk.Label(header, textvariable=self.status_var, font=("Arial", 12)).pack(side=tk.RIGHT)

        # Système d'onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Créer les tabs
        self.create_tabs()

    def create_tabs(self):
        """Crée les onglets de l'interface"""
        # Tab 1: Portfolio
        self.portfolio_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.portfolio_tab, text="📊 Portfolio")

        # Tab 2: Outils (Converter)
        self.tools_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tools_tab, text="🔧 Outils")

        # Tab 3: TWR Analytics
        self.twr_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.twr_tab, text="📈 TWR Analytics")

        # Créer le contenu du tab Portfolio
        self.create_portfolio_ui()

    def create_portfolio_ui(self):
        """Crée l'interface principale du portfolio dans son tab"""
        # Section Portfolio dans son tab
        balance_frame = ttk.LabelFrame(self.portfolio_tab, text="Portfolio Holdings", padding="10")
        balance_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.total_var = tk.StringVar(value="Total: $0.00")
        ttk.Label(balance_frame, textvariable=self.total_var, font=("Arial", 12, "bold")).pack(anchor=tk.W)

        columns = ('Actif', 'Balance', 'Valeur USD', '% Portfolio')
        self.balance_tree = ttk.Treeview(balance_frame, columns=columns, show='headings', height=20)
        for col in columns:
            self.balance_tree.heading(col, text=col)
            self.balance_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(balance_frame, orient=tk.VERTICAL, command=self.balance_tree.yview)
        self.balance_tree.configure(yscrollcommand=scrollbar.set)
        self.balance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_config(self):
        env_vars = EnvLoader.load_env()
        if env_vars.get('BINANCE_API_KEY') and env_vars.get('BINANCE_API_SECRET'):
            try:
                self.trader = BinanceTrader(
                    env_vars['BINANCE_API_KEY'],
                    env_vars['BINANCE_API_SECRET'],
                    env_vars.get('BINANCE_TESTNET', 'false').lower() == 'true'
                )
                self.portfolio_manager = PortfolioManager(self.trader)

                # Initialiser les modules refactorisés
                self.init_modules()
                self.test_connection()
            except Exception as e:
                logger.error(f"Erreur init: {e}")
                messagebox.showerror("Erreur", f"Erreur de configuration: {e}")

    def init_modules(self):
        """Initialise les modules refactorisés et crée leurs interfaces dans les tabs"""
        if not self.trader:
            return

        try:
            # Portfolio Configuration (dans le tab Outils)
            self.portfolio_config = PortfolioConfig(self.trader, self.portfolio_manager)
            config_frame = self.portfolio_config.create_config_ui(
                self.tools_tab,
                self.refresh_balances,
                None  # Plus besoin du callback de frais
            )


            # Performance Analytics (uniquement dans le tab TWR Analytics)
            self.performance_interface = PerformanceInterface(self.trader)

            # Créer le contenu du tab TWR Analytics avec boutons intégrés
            self.create_twr_tab_content()

        except Exception as e:
            logger.error(f"Erreur initialisation modules: {e}")
            messagebox.showerror("Erreur", f"Erreur initialisation: {e}")

    def create_twr_tab_content(self):
        """Crée le contenu du tab TWR Analytics"""
        if not self.performance_interface:
            return

        # Créer une version intégrée de TWRAnalyticsWindow dans le tab
        self.twr_analytics = TWRAnalyticsTab(self.twr_tab, self.performance_interface.tracker)


    def refresh_twr_if_needed(self):
        """Actualise le TWR si le tab est initialisé"""
        if hasattr(self, 'twr_analytics'):
            self.twr_analytics.refresh_all_data()


    def test_connection(self):
        def test():
            if self.trader and self.trader.test_connection():
                self.status_var.set("✅ Connecté")
                self.refresh_balances()
            else:
                self.status_var.set("❌ Erreur connexion")
        threading.Thread(target=test, daemon=True).start()

    def start_auto_refresh(self):
        def refresh_loop():
            if self.trader:
                try:
                    self.all_balances = self.trader.get_all_balances_usd(5.0)
                    self.root.after(0, self.update_display)
                except Exception as e:
                    logger.error(f"Auto-refresh error: {e}")
            self.root.after(10000, refresh_loop)  # 30 secondes
        self.root.after(2000, refresh_loop)  # Premier refresh dans 5s

    def refresh_balances(self):
        def refresh():
            try:
                self.all_balances = self.trader.get_all_balances_usd(5.0)
                self.root.after(0, self.update_display)
            except Exception as e:
                logger.error(f"Refresh error: {e}")
        threading.Thread(target=refresh, daemon=True).start()

    def update_display(self):
        # Vider l'arbre
        for item in self.balance_tree.get_children():
            self.balance_tree.delete(item)

        total_usd = sum(b['usd_value'] for b in self.all_balances.values())
        self.total_var.set(f"Total Portfolio: ${total_usd:.2f}")

        # Ajouter les balances triées
        for asset, data in sorted(self.all_balances.items(), key=lambda x: x[1]['usd_value'], reverse=True):
            percent = (data['usd_value'] / total_usd * 100) if total_usd > 0 else 0
            self.balance_tree.insert('', 'end', values=(
                asset,
                f"{data['balance']:.6f}",
                f"${data['usd_value']:.2f}",
                f"{percent:.2f}%"
            ))


        # Gérer les snapshots si performance tracker initialisé
        if self.performance_interface:
            # Si c'est le premier rafraîchissement, prendre snapshot après données chargées
            if not self.performance_interface.first_refresh_done:
                logger.info("📊 Premier rafraîchissement terminé - vérification snapshot...")
                self.performance_interface.first_refresh_done = True
                self.performance_interface.check_and_take_snapshot_after_refresh()

            # Actualiser automatiquement le TWR dans son tab
            self.refresh_twr_if_needed()



class TWRAnalyticsTab:
    """Version intégrée de TWRAnalyticsWindow pour le système d'onglets"""

    def __init__(self, parent_tab, tracker):
        self.parent = parent_tab
        self.tracker = tracker

        # Variables d'affichage pour toutes les périodes
        self.twr_7d = tk.StringVar(value="Calcul...")
        self.twr_14d = tk.StringVar(value="Calcul...")
        self.twr_30d = tk.StringVar(value="Calcul...")
        self.twr_60d = tk.StringVar(value="Calcul...")
        self.twr_90d = tk.StringVar(value="Calcul...")
        self.twr_180d = tk.StringVar(value="Calcul...")
        self.twr_360d = tk.StringVar(value="Calcul...")
        self.twr_720d = tk.StringVar(value="Calcul...")
        self.twr_total = tk.StringVar(value="Calcul...")

        self.annualized_7d = tk.StringVar(value="--")
        self.annualized_14d = tk.StringVar(value="--")
        self.annualized_30d = tk.StringVar(value="--")
        self.annualized_60d = tk.StringVar(value="--")
        self.annualized_90d = tk.StringVar(value="--")
        self.annualized_180d = tk.StringVar(value="--")
        self.annualized_360d = tk.StringVar(value="--")
        self.annualized_720d = tk.StringVar(value="--")
        # Pas d'annualisation pour total et périodes > 365j

        self.cash_flow_info = tk.StringVar(value="Chargement cash flows...")
        self.snapshot_info = tk.StringVar(value="Chargement snapshots...")

        self.create_ui()
        self.refresh_all_data()

    def create_ui(self):
        """Crée l'interface dans le tab"""
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Titre
        title_label = ttk.Label(main_frame, text="📊 Time-Weighted Return Analytics",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Section TWR
        twr_frame = ttk.LabelFrame(main_frame, text="📈 TWR par période", padding="10")
        twr_frame.pack(fill=tk.X, pady=(0, 10))

        # Headers
        headers_frame = ttk.Frame(twr_frame)
        headers_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(headers_frame, text="Période", font=("Arial", 10, "bold"), width=12).pack(side=tk.LEFT)
        ttk.Label(headers_frame, text="TWR", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT)
        ttk.Label(headers_frame, text="Annualisé", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT)

        # Créer toutes les lignes de périodes
        periods_data = [
            ("7 jours", self.twr_7d, self.annualized_7d),
            ("14 jours", self.twr_14d, self.annualized_14d),
            ("30 jours", self.twr_30d, self.annualized_30d),
            ("60 jours", self.twr_60d, self.annualized_60d),
            ("90 jours", self.twr_90d, self.annualized_90d),
            ("180 jours", self.twr_180d, self.annualized_180d),
            ("360 jours", self.twr_360d, self.annualized_360d),
            ("720 jours", self.twr_720d, self.annualized_720d),
            ("Total", self.twr_total, None)  # Pas d'annualisation pour total
        ]

        for period_name, twr_var, ann_var in periods_data:
            row = ttk.Frame(twr_frame)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=period_name, width=12).pack(side=tk.LEFT)
            ttk.Label(row, textvariable=twr_var, width=15, font=("Arial", 10, "bold")).pack(side=tk.LEFT)

            if ann_var:
                ttk.Label(row, textvariable=ann_var, width=15).pack(side=tk.LEFT)
            else:
                ttk.Label(row, text="--", width=15).pack(side=tk.LEFT)


        # Section Données
        data_frame = ttk.LabelFrame(main_frame, text="📋 Données de base", padding="10")
        data_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(data_frame, textvariable=self.snapshot_info,
                 font=("Arial", 9)).pack(anchor=tk.W, pady=2)
        ttk.Label(data_frame, textvariable=self.cash_flow_info,
                 font=("Arial", 9)).pack(anchor=tk.W, pady=2)


        # Boutons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(buttons_frame, text="🔄 Actualiser",
                  command=self.refresh_all_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="➕ Ajouter snapshot",
                  command=self.add_manual_snapshot).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="💰 Ajouter cash flow",
                  command=self.add_manual_cash_flow).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="📤 Exporter",
                  command=self.export_data).pack(side=tk.LEFT, padx=5)

    def generate_test_data(self):
        """Génère des données de test"""
        def generate():
            try:
                success = self.tracker.generate_fake_data_for_testing()
                if success:
                    messagebox.showinfo("Succès", "Données de test générées!\nVous pouvez maintenant tester le TWR.")
                    # Actualiser les métriques après génération
                    self.refresh_all_data()
                else:
                    messagebox.showerror("Erreur", "Échec de génération des données de test")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur génération: {e}")

        threading.Thread(target=generate, daemon=True).start()

    def refresh_all_data(self):
        """Actualise toutes les données du tab"""
        def calculate():
            try:
                # Stats générales
                stats = self.tracker.get_tracking_stats()
                days_available = stats['days']

                # Snapshots info
                snapshots = self.tracker.db.get_snapshots()
                self.snapshot_info.set(f"📸 {len(snapshots)} snapshots depuis {days_available} jours")

                # Cash flows info
                cash_flows = self.tracker.db.get_cash_flows()
                total_deposits = sum(cf['amount'] for cf in cash_flows if cf['amount'] > 0)
                total_withdraws = sum(abs(cf['amount']) for cf in cash_flows if cf['amount'] < 0)
                self.cash_flow_info.set(f"💰 {len(cash_flows)} cash flows: +${total_deposits:.0f} / -${total_withdraws:.0f}")

                # Calculer TWR pour toutes les périodes
                periods = [7, 14, 30, 60, 90, 180, 360, 720]
                twr_vars = [
                    self.twr_7d, self.twr_14d, self.twr_30d, self.twr_60d,
                    self.twr_90d, self.twr_180d, self.twr_360d, self.twr_720d
                ]
                ann_vars = [
                    self.annualized_7d, self.annualized_14d, self.annualized_30d, self.annualized_60d,
                    self.annualized_90d, self.annualized_180d, self.annualized_360d, self.annualized_720d
                ]

                for i, days in enumerate(periods):
                    if days_available >= days:
                        metrics = self.tracker.calculate_performance_metrics(days)

                        if metrics and metrics['twr'] is not None:
                            twr = metrics['twr'] * 100
                            emoji = "📈" if twr > 0 else "📉" if twr < 0 else "➡️"
                            twr_vars[i].set(f"{emoji} {twr:+.2f}%")

                            # Annualisation seulement si <= 365 jours
                            if days <= 365 and metrics['twr_annualized'] is not None:
                                ann_twr = metrics['twr_annualized'] * 100
                                ann_vars[i].set(f"{ann_twr:+.1f}%")
                            else:
                                ann_vars[i].set("--")
                        else:
                            twr_vars[i].set("❌ N/A")
                            ann_vars[i].set("--")
                    else:
                        twr_vars[i].set(f"⏳ {days - days_available}j restants")
                        ann_vars[i].set("--")

                # Calculer TWR total (toute la période disponible)
                if days_available > 0:
                    total_metrics = self.tracker.calculate_performance_metrics(days_available)
                    if total_metrics and total_metrics['twr'] is not None:
                        total_twr = total_metrics['twr'] * 100
                        emoji = "📈" if total_twr > 0 else "📉" if total_twr < 0 else "➡️"
                        self.twr_total.set(f"{emoji} {total_twr:+.2f}% ({days_available}j)")
                    else:
                        self.twr_total.set("❌ N/A")
                else:
                    self.twr_total.set("⏳ Pas de données")

            except Exception as e:
                logger.error(f"Erreur refresh TWR tab: {e}")

        threading.Thread(target=calculate, daemon=True).start()

    def add_manual_snapshot(self):
        """Interface pour ajouter manuellement un snapshot"""
        # Créer une fenêtre de saisie
        snapshot_window = tk.Toplevel()
        snapshot_window.title("➕ Ajouter Snapshot Manuel")
        snapshot_window.geometry("400x300")

        ttk.Label(snapshot_window, text="Ajouter un snapshot du portfolio", font=("Arial", 12, "bold")).pack(pady=10)

        # Obtenir le portfolio actuel pour pré-remplir
        try:
            balances = self.tracker.trader.get_all_balances_usd(1.0)
            total_value = sum(b['usd_value'] for b in balances.values())

            # Formulaire
            ttk.Label(snapshot_window, text=f"Valeur totale actuelle: ${total_value:.2f}").pack(pady=5)

            ttk.Label(snapshot_window, text="Confirmer l'ajout de ce snapshot?").pack(pady=10)

            def save_snapshot():
                try:
                    # Simplifier la composition
                    composition = {}
                    for asset, data in balances.items():
                        if data['usd_value'] > 1.0:
                            composition[asset] = {
                                'balance': data['balance'],
                                'usd_value': data['usd_value'],
                                'percentage': (data['usd_value'] / total_value * 100) if total_value > 0 else 0
                            }

                    self.tracker.db.add_snapshot_manually(datetime.now(), total_value, composition)
                    messagebox.showinfo("Succès", "Snapshot ajouté avec succès!")
                    snapshot_window.destroy()
                    self.refresh_all_data()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur ajout snapshot: {e}")

            ttk.Button(snapshot_window, text="✅ Confirmer", command=save_snapshot).pack(pady=10)
            ttk.Button(snapshot_window, text="❌ Annuler", command=snapshot_window.destroy).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'obtenir le portfolio: {e}")
            snapshot_window.destroy()

    def add_manual_cash_flow(self):
        """Interface pour ajouter manuellement un cash flow"""
        # Créer une fenêtre de saisie
        cash_flow_window = tk.Toplevel()
        cash_flow_window.title("💰 Ajouter Cash Flow Manuel")
        cash_flow_window.geometry("400x350")

        ttk.Label(cash_flow_window, text="Ajouter un cash flow (dépôt/retrait)", font=("Arial", 12, "bold")).pack(pady=10)

        # Formulaire
        form_frame = ttk.Frame(cash_flow_window)
        form_frame.pack(pady=10, padx=20, fill=tk.X)

        # Type de cash flow
        ttk.Label(form_frame, text="Type d'opération:").grid(row=0, column=0, sticky=tk.W, pady=5)
        type_var = tk.StringVar(value="DEPOSIT")
        type_combo = ttk.Combobox(form_frame, textvariable=type_var, values=["DEPOSIT", "WITHDRAW"], state="readonly", width=15)
        type_combo.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Montant
        ttk.Label(form_frame, text="Montant (EUR):").grid(row=1, column=0, sticky=tk.W, pady=5)
        amount_var = tk.StringVar()
        amount_entry = ttk.Entry(form_frame, textvariable=amount_var, width=18)
        amount_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Date et heure (par défaut maintenant)
        ttk.Label(form_frame, text="Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(form_frame, textvariable=date_var, width=18)
        date_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

        ttk.Label(form_frame, text="Heure:").grid(row=3, column=0, sticky=tk.W, pady=5)
        time_var = tk.StringVar(value=datetime.now().strftime("%H:%M"))
        time_entry = ttk.Entry(form_frame, textvariable=time_var, width=18)
        time_entry.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Description
        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(form_frame, textvariable=desc_var, width=18)
        desc_entry.grid(row=4, column=1, sticky=tk.W, pady=5)

        # Instructions
        instructions = ttk.Label(cash_flow_window,
                                text="💡 Workflow optimal:\n1. Prendre snapshot AVANT l'opération\n2. Faire dépôt/retrait EUR↔USDC\n3. Ajouter ce cash flow\n4. Snapshots auto continuent toutes les 2h",
                                font=("Arial", 9), foreground="gray", justify=tk.LEFT)
        instructions.pack(pady=10)

        def save_cash_flow():
            try:
                # Validation
                if not amount_var.get():
                    messagebox.showerror("Erreur", "Veuillez entrer un montant")
                    return

                amount = float(amount_var.get())
                if amount <= 0:
                    messagebox.showerror("Erreur", "Le montant doit être positif")
                    return

                # Construire la datetime
                date_str = f"{date_var.get()} {time_var.get()}"
                timestamp = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

                # Convertir en USD (pour withdraw, rendre négatif)
                amount_usd = amount if type_var.get() == "DEPOSIT" else -amount

                # Description par défaut
                description = desc_var.get() or f"{type_var.get()} manuel EUR→USDC"

                # Sauvegarder
                self.tracker.db.save_cash_flow(timestamp, amount_usd, type_var.get(), description)

                messagebox.showinfo("Succès", f"Cash flow ajouté: {amount_usd:+.2f}€ le {timestamp}")
                cash_flow_window.destroy()
                self.refresh_all_data()

            except ValueError:
                messagebox.showerror("Erreur", "Montant invalide ou format de date incorrect")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur sauvegarde: {e}")

        # Boutons
        buttons_frame = ttk.Frame(cash_flow_window)
        buttons_frame.pack(pady=20)

        ttk.Button(buttons_frame, text="✅ Sauvegarder", command=save_cash_flow).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="❌ Annuler", command=cash_flow_window.destroy).pack(side=tk.LEFT, padx=10)

        # Focus sur le montant
        amount_entry.focus()

    def export_data(self):
        """Exporte les données TWR"""
        messagebox.showinfo("Export", "Fonctionnalité d'export à venir!")


def main():
    root = tk.Tk()
    app = TradingApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: root.destroy() if messagebox.askokcancel("Quitter", "Fermer l'application?") else None)
    root.mainloop()

if __name__ == "__main__":
    main()
