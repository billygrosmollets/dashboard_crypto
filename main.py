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
from config_converter import PortfolioConfig, CryptoConverter

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

        self.setup_ui()
        self.load_config()
        self.start_auto_refresh()

    def setup_ui(self):
        # Header avec statut
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header, text="🚀 Binance Portfolio", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="❌ Déconnecté")
        ttk.Label(header, textvariable=self.status_var, font=("Arial", 12)).pack(side=tk.RIGHT)

        # Les interfaces seront créées lors de l'initialisation des modules
        # Placeholder pour les sections qui seront ajoutées dynamiquement

        # Section Portfolio principale (toujours présente)
        self.create_portfolio_ui()

    def create_portfolio_ui(self):
        """Crée l'interface principale du portfolio"""
        balance_frame = ttk.LabelFrame(self.root, text="Portfolio", padding="10")
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
        """Initialise les modules refactorisés et crée leurs interfaces"""
        if not self.trader:
            return

        try:
            # Portfolio Configuration
            self.portfolio_config = PortfolioConfig(self.trader, self.portfolio_manager)
            config_frame = self.portfolio_config.create_config_ui(self.root, self.refresh_balances)

            # Crypto Converter
            self.crypto_converter = CryptoConverter(self.trader)
            converter_frame = self.crypto_converter.create_converter_ui(
                self.root,
                lambda: self.all_balances,
                self.refresh_balances
            )

            # Réorganiser l'ordre des frames (portfolio en bas)
            config_frame.pack_configure(before=converter_frame)

        except Exception as e:
            logger.error(f"Erreur initialisation modules: {e}")
            messagebox.showerror("Erreur", f"Erreur initialisation: {e}")


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

        # Mettre à jour le convertisseur s'il existe
        if self.crypto_converter:
            self.crypto_converter.update_owned_assets()


def main():
    root = tk.Tk()
    app = TradingApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: root.destroy() if messagebox.askokcancel("Quitter", "Fermer l'application?") else None)
    root.mainloop()

if __name__ == "__main__":
    main()
