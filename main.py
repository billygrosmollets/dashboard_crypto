#!/usr/bin/env python3
"""
Binance Advanced Trading Platform - Version Compacte
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
                    # Pour les achats, calculer le quoteOrderQty
                    ticker = self.client.get_symbol_ticker(symbol=symbol)
                    quote_qty = amount * float(ticker['price'])
                    order = self.client.order_market_buy(symbol=symbol, quoteOrderQty=round(quote_qty, 2))

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
                logger.error(f"Symbole non permis pour ce compte: {from_asset}->{to_asset}")
            else:
                logger.error(f"Erreur API Binance: {e}")
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

class PnLTracker:
    def __init__(self, trader):
        self.trader = trader

    def get_account_snapshot_history(self, days):
        """Récupère les snapshots de compte pour les N derniers jours"""
        try:
            snapshots = []
            for i in range(days):
                timestamp = int((datetime.now() - timedelta(days=i)).timestamp() * 1000)
                snapshot = self.trader.client.get_account_snapshot(type='SPOT', startTime=timestamp, limit=1)
                if snapshot['snapshotVos']:
                    snapshots.append({
                        'date': datetime.fromtimestamp(snapshot['snapshotVos'][0]['updateTime'] / 1000),
                        'balances': snapshot['snapshotVos'][0]['data']['balances']
                    })
            return snapshots
        except Exception as e:
            logger.error(f"Erreur récupération snapshots: {e}")
            return []

    def calculate_portfolio_value_at_date(self, balances, target_date):
        """Calcule la valeur du portfolio à une date donnée"""
        try:
            total_usd_value = 0

            for balance in balances:
                asset = balance['asset']
                amount = float(balance['free']) + float(balance['locked'])

                if amount <= 0:
                    continue

                # Pour les stablecoins, valeur = montant
                if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
                    total_usd_value += amount
                else:
                    # Récupérer le prix historique
                    price_usd = self.get_historical_price(asset, target_date)
                    total_usd_value += amount * price_usd

            return total_usd_value
        except Exception as e:
            logger.error(f"Erreur calcul valeur portfolio: {e}")
            return 0

    def get_historical_price(self, asset, target_date):
        """Récupère le prix historique d'un actif à une date donnée"""
        try:
            # Essayer avec USDT en premier
            for quote in ['USDT', 'USDC', 'BUSD']:
                symbol = f"{asset}{quote}"
                if symbol in self.trader.all_symbols:
                    # Utiliser klines pour obtenir le prix à cette date
                    start_time = int(target_date.timestamp() * 1000)
                    end_time = start_time + (24 * 60 * 60 * 1000)  # +24h

                    klines = self.trader.client.get_klines(
                        symbol=symbol,
                        interval='1d',
                        startTime=start_time,
                        endTime=end_time,
                        limit=1
                    )

                    if klines:
                        # Utiliser le prix de clôture
                        return float(klines[0][4])

            return 0
        except Exception as e:
            logger.error(f"Erreur prix historique {asset}: {e}")
            return 0

    def get_all_trades_in_period(self, days):
        """Récupère tous les trades sur une période donnée"""
        try:
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            all_trades = []

            # Approche plus large : chercher dans tous les symboles populaires
            # au lieu de se limiter aux balances actuelles
            popular_assets = [
                'BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'DOGE', 'AVAX',
                'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ALGO', 'ATOM', 'ICP',
                'FIL', 'TRX', 'ETC', 'XLM', 'VET', 'THETA', 'FTT', 'MANA',
                'SAND', 'AXS', 'SHIB', 'CRV', 'BAT', 'COMP', 'MKR', 'YFI',
                'SUSHI', 'SNX', 'AAVE', 'NEAR', 'FTM', 'LRC', 'ENJ', 'CHZ',
                'GALA', 'HBAR', 'FLOW', 'ILV', 'RUNE', 'KSM', 'KAVA', 'SRM',
                'RAY', 'GMT', 'APE', 'PEOPLE', 'JASMY', 'DYDX', 'OP', 'APT',
                'ROSE', 'GMX', 'MAGIC', 'BLUR', 'SUI', 'ARB', 'ID', 'RDNT',
                'JOE', 'HOOK', 'GAS', 'LQTY', 'MAVERICK', 'EDU', 'CYBER',
                'ARK', 'GFT', 'USTC', 'SEI', 'CYBER', 'MEME', 'ORDI',
                'VIRTUAL', 'ONDO', 'PENGU', 'TAO', 'USUAL', 'MOVE'
            ]

            # Ajouter aussi les actifs avec des balances actuelles
            account = self.trader.client.get_account()
            for balance in account['balances']:
                asset = balance['asset']
                total = float(balance['free']) + float(balance['locked'])
                if total > 0:
                    popular_assets.append(asset)

            # Enlever les doublons
            unique_assets = list(set(popular_assets))

            logger.info(f"Recherche trades sur {len(unique_assets)} actifs pour {days} jours")

            # Pour chaque actif, chercher les paires de trading possibles
            for asset in unique_assets:
                for quote in ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'BNB', 'FDUSD']:
                    for symbol in [f"{asset}{quote}", f"{quote}{asset}"]:
                        if symbol in self.trader.all_symbols:
                            try:
                                trades = self.trader.client.get_my_trades(
                                    symbol=symbol,
                                    startTime=start_time,
                                    limit=1000
                                )
                                if trades:
                                    all_trades.extend(trades)
                                    logger.debug(f"Trouvé {len(trades)} trades pour {symbol}")
                            except Exception as e:
                                logger.debug(f"Pas de trades pour {symbol}: {e}")
                                continue

            # Trier par timestamp
            all_trades.sort(key=lambda x: x['time'])
            return all_trades

        except Exception as e:
            logger.error(f"Erreur récupération trades: {e}")
            return []

    def calculate_pnl_from_trades(self, days):
        """Calcule le P&L réel basé sur l'historique des trades"""
        try:
            trades = self.get_all_trades_in_period(days)

            if not trades:
                return {'realized_pnl': 0, 'total_fees': 0, 'trade_count': 0}

            total_realized_pnl = 0
            total_fees_usdt = 0
            trade_count = len(trades)

            # Regrouper les trades par actif
            asset_trades = {}

            for trade in trades:
                symbol = trade['symbol']
                is_buyer = trade['isBuyer']
                qty = float(trade['qty'])
                price = float(trade['price'])
                fee = float(trade['commission'])
                fee_asset = trade['commissionAsset']
                trade_time = int(trade['time'])

                # Déterminer l'actif de base et de cotation
                base_asset = symbol[:-4] if symbol.endswith('USDT') else symbol[:-3]
                quote_asset = symbol[-4:] if symbol.endswith('USDT') else symbol[-3:]

                if base_asset not in asset_trades:
                    asset_trades[base_asset] = []

                # Convertir les frais en USDT
                fee_usdt = 0
                if fee_asset in ['USDT', 'USDC', 'BUSD']:
                    fee_usdt = fee
                elif fee_asset == 'BNB':
                    # Obtenir le prix BNB au moment du trade (approximation avec prix actuel)
                    try:
                        bnb_price = float(self.trader.client.get_symbol_ticker(symbol='BNBUSDT')['price'])
                        fee_usdt = fee * bnb_price
                    except:
                        fee_usdt = fee * 300  # Prix approximatif BNB

                total_fees_usdt += fee_usdt

                asset_trades[base_asset].append({
                    'is_buy': is_buyer,
                    'qty': qty,
                    'price': price,
                    'quote_asset': quote_asset,
                    'fee_usdt': fee_usdt,
                    'time': trade_time
                })

            # Calculer le P&L réalisé pour chaque actif
            for asset, trades_list in asset_trades.items():
                # Trier par temps
                trades_list.sort(key=lambda x: x['time'])

                # FIFO (First In, First Out) pour calculer le P&L réalisé
                buy_queue = []  # [(qty, price_usdt)]

                for trade in trades_list:
                    qty = trade['qty']
                    price = trade['price']
                    quote_asset = trade['quote_asset']

                    # Convertir le prix en USDT si nécessaire
                    if quote_asset == 'USDT':
                        price_usdt = price
                    elif quote_asset == 'BTC':
                        # Approximation : utiliser prix BTC actuel
                        try:
                            btc_price = float(self.trader.client.get_symbol_ticker(symbol='BTCUSDT')['price'])
                            price_usdt = price * btc_price
                        except:
                            price_usdt = price * 50000  # Prix approximatif
                    else:
                        price_usdt = price  # Approximation

                    if trade['is_buy']:
                        # Achat : ajouter à la queue
                        buy_queue.append((qty, price_usdt))
                    else:
                        # Vente : calculer P&L réalisé
                        remaining_to_sell = qty

                        while remaining_to_sell > 0 and buy_queue:
                            buy_qty, buy_price_usdt = buy_queue[0]

                            if buy_qty <= remaining_to_sell:
                                # Vendre tout ce lot d'achat
                                pnl = buy_qty * (price_usdt - buy_price_usdt)
                                total_realized_pnl += pnl
                                remaining_to_sell -= buy_qty
                                buy_queue.pop(0)
                            else:
                                # Vendre une partie de ce lot d'achat
                                pnl = remaining_to_sell * (price_usdt - buy_price_usdt)
                                total_realized_pnl += pnl
                                buy_queue[0] = (buy_qty - remaining_to_sell, buy_price_usdt)
                                remaining_to_sell = 0

            return {
                'realized_pnl': total_realized_pnl,
                'total_fees': total_fees_usdt,
                'trade_count': trade_count,
                'net_pnl': total_realized_pnl - total_fees_usdt
            }

        except Exception as e:
            logger.error(f"Erreur calcul P&L trades: {e}")
            return {'realized_pnl': 0, 'total_fees': 0, 'trade_count': 0, 'net_pnl': 0}

    def calculate_pnl_periods(self):
        """Calcule le P&L pour les périodes 7, 30, 365 jours basé sur les trades réels"""
        try:
            results = {}

            for period in [7, 30, 365]:
                try:
                    pnl_data = self.calculate_pnl_from_trades(period)

                    results[f'{period}d'] = {
                        'absolute': pnl_data['net_pnl'],
                        'percentage': 0,  # Difficile à calculer sans valeur de base
                        'realized_pnl': pnl_data['realized_pnl'],
                        'total_fees': pnl_data['total_fees'],
                        'trade_count': pnl_data['trade_count']
                    }

                except Exception as e:
                    logger.error(f"Erreur calcul P&L {period}d: {e}")
                    results[f'{period}d'] = {
                        'absolute': 0,
                        'percentage': 0,
                        'realized_pnl': 0,
                        'total_fees': 0,
                        'trade_count': 0
                    }

            return results

        except Exception as e:
            logger.error(f"Erreur calcul P&L global: {e}")
            return {}

    def get_deposit_withdraw_summary(self, days):
        """Récupère un résumé des dépôts/retraits sur N jours"""
        try:
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            # Dépôts
            deposits = self.trader.client.get_deposit_history(startTime=start_time)
            total_deposits = 0
            for deposit in deposits:
                if deposit['status'] == 1:  # Réussi
                    # Convertir en USD approximatif
                    amount = float(deposit['amount'])
                    if deposit['coin'] in ['USDT', 'USDC', 'BUSD']:
                        total_deposits += amount
                    # Pour les autres cryptos, on pourrait ajouter une conversion

            # Retraits
            withdraws = self.trader.client.get_withdraw_history(startTime=start_time)
            total_withdraws = 0
            for withdraw in withdraws:
                if withdraw['status'] == 6:  # Réussi
                    amount = float(withdraw['amount'])
                    if withdraw['coin'] in ['USDT', 'USDC', 'BUSD']:
                        total_withdraws += amount

            return {
                'deposits': total_deposits,
                'withdraws': total_withdraws,
                'net_flow': total_deposits - total_withdraws
            }

        except Exception as e:
            logger.error(f"Erreur historique dépôts/retraits: {e}")
            return {'deposits': 0, 'withdraws': 0, 'net_flow': 0}

    def get_recent_orders_method(self, days):
        """Méthode alternative: récupérer via les ordres récents"""
        try:
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            # Récupérer tous les ordres récents (toutes paires)
            all_orders = self.trader.client.get_all_orders(limit=1000)

            # Filtrer par date et statut
            relevant_orders = []
            for order in all_orders:
                if (order['time'] >= start_time and
                    order['status'] == 'FILLED'):
                    relevant_orders.append(order)

            print(f"Méthode ordres: {len(relevant_orders)} ordres remplis trouvés")
            return relevant_orders

        except Exception as e:
            logger.error(f"Erreur méthode ordres: {e}")
            return []

    def debug_pnl_calculation(self, days=7):
        """Méthode de debug pour analyser le calcul P&L"""
        try:
            print(f"\n=== DEBUG P&L {days} jours ===")

            trades = self.get_all_trades_in_period(days)
            print(f"Nombre de trades trouvés: {len(trades)}")

            if not trades:
                print("Aucun trade trouvé dans cette période")
                return

            # Afficher la répartition des dates
            if len(trades) > 0:
                earliest = min(trade['time'] for trade in trades)
                latest = max(trade['time'] for trade in trades)
                print(f"Période réelle des trades: {datetime.fromtimestamp(earliest/1000)} -> {datetime.fromtimestamp(latest/1000)}")

            # Afficher les premiers trades pour debug
            print("\nPremiers trades:")
            for i, trade in enumerate(trades[:10]):
                trade_time = datetime.fromtimestamp(trade['time']/1000).strftime('%Y-%m-%d %H:%M')
                print(f"  {i+1}. [{trade_time}] {trade['symbol']} - {'BUY' if trade['isBuyer'] else 'SELL'} - "
                      f"{trade['qty']} @ {trade['price']} - Fee: {trade['commission']} {trade['commissionAsset']}")

            # Grouper par symbol
            symbols = {}
            total_volume = 0
            for trade in trades:
                symbol = trade['symbol']
                if symbol not in symbols:
                    symbols[symbol] = {'count': 0, 'volume': 0}
                symbols[symbol]['count'] += 1
                symbols[symbol]['volume'] += float(trade['qty']) * float(trade['price'])
                total_volume += float(trade['qty']) * float(trade['price'])

            print(f"\nSymboles tradés: {len(symbols)}")
            for symbol, data in sorted(symbols.items(), key=lambda x: x[1]['volume'], reverse=True)[:10]:
                print(f"  {symbol}: {data['count']} trades, ${data['volume']:.2f} volume")

            print(f"\nVolume total tradé: ${total_volume:.2f}")

            # Calculer et afficher le détail
            pnl_data = self.calculate_pnl_from_trades(days)
            print(f"\nRésultats:")
            print(f"  P&L réalisé: ${pnl_data['realized_pnl']:.2f}")
            print(f"  Frais totaux: ${pnl_data['total_fees']:.2f}")
            print(f"  P&L net: ${pnl_data['net_pnl']:.2f}")
            print(f"  Nombre de trades: {pnl_data['trade_count']}")

            # Comparaison avec ce que Binance affiche
            expected_values = {7: -41.16, 30: 237.68, 365: 859.69}
            if days in expected_values:
                expected = expected_values[days]
                difference = pnl_data['net_pnl'] - expected
                print(f"\n🎯 Comparaison avec Binance:")
                print(f"  Attendu: ${expected:.2f}")
                print(f"  Calculé: ${pnl_data['net_pnl']:.2f}")
                print(f"  Différence: ${difference:.2f}")

        except Exception as e:
            print(f"Erreur debug: {e}")

# ============================================================================
# APPLICATION PRINCIPALE COMPACTE
# ============================================================================

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Binance Trading Platform")
        self.root.geometry("950x800")
        
        # Variables
        self.trader = None
        self.portfolio_manager = None
        self.pnl_tracker = None
        self.all_balances = {}
        self.portfolio_config = {'btc_percent': 20, 'usdc_percent': 40, 'altcoin_percent': 40}
        self.conversion_rate_var = tk.StringVar(value="Taux: --")
        self.conversion_result_var = tk.StringVar(value="")
        self.conversion_fees_var = tk.StringVar(value="")
        self.available_balance_var = tk.StringVar(value="")

        # Variables P&L
        self.pnl_7d_var = tk.StringVar(value="7j: --")
        self.pnl_30d_var = tk.StringVar(value="30j: --")
        self.pnl_365d_var = tk.StringVar(value="365j: --")
        
        self.setup_ui()
        self.load_config()
        self.start_auto_refresh()

    def setup_ui(self):
        # Header avec statut
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header, text="🚀 Binance Trading", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="❌ Déconnecté")
        ttk.Label(header, textvariable=self.status_var, font=("Arial", 12)).pack(side=tk.RIGHT)

        # Configuration portfolio
        config_frame = ttk.LabelFrame(self.root, text="Configuration Portfolio", padding="10")
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(config_frame, text="BTC %:").grid(row=0, column=0, padx=5)
        self.btc_var = tk.StringVar(value="20")
        ttk.Entry(config_frame, textvariable=self.btc_var, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(config_frame, text="USDC %:").grid(row=0, column=2, padx=5)
        self.usdc_var = tk.StringVar(value="40")
        ttk.Entry(config_frame, textvariable=self.usdc_var, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Label(config_frame, text="Altcoins %:").grid(row=0, column=4, padx=5)
        self.alt_var = tk.StringVar(value="40")
        ttk.Entry(config_frame, textvariable=self.alt_var, width=8).grid(row=0, column=5, padx=5)
        
        ttk.Button(config_frame, text="⚡ Rééquilibrer", command=self.execute_rebalancing).grid(row=0, column=6, padx=20)

        # Section P&L
        pnl_frame = ttk.LabelFrame(self.root, text="📈 Profits & Pertes", padding="10")
        pnl_frame.pack(fill=tk.X, padx=10, pady=5)

        # Première ligne - P&L périodes
        pnl_row1 = ttk.Frame(pnl_frame)
        pnl_row1.pack(fill=tk.X, pady=2)

        ttk.Label(pnl_row1, textvariable=self.pnl_7d_var, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        ttk.Label(pnl_row1, textvariable=self.pnl_30d_var, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        ttk.Label(pnl_row1, textvariable=self.pnl_365d_var, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)

        # Boutons pour P&L
        ttk.Button(pnl_row1, text="🔄 Actualiser P&L", command=self.refresh_pnl).pack(side=tk.RIGHT, padx=5)
        ttk.Button(pnl_row1, text="🐛 Debug P&L", command=self.debug_pnl).pack(side=tk.RIGHT, padx=5)

        # Interface de conversion universelle
        conversion_frame = ttk.LabelFrame(self.root, text="🔄 Convertisseur Crypto Universal", padding="10")
        conversion_frame.pack(fill=tk.X, padx=10, pady=5)

        # Première ligne: DE et VERS
        from_frame = ttk.Frame(conversion_frame)
        from_frame.pack(fill=tk.X, pady=2)

        ttk.Label(from_frame, text="De:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.from_asset_var = tk.StringVar()
        self.from_combo = ttk.Combobox(from_frame, textvariable=self.from_asset_var, width=12, state="readonly")
        self.from_combo.pack(side=tk.LEFT, padx=5)
        self.from_combo.bind('<<ComboboxSelected>>', self.update_conversion_rate)

        # Affichage de la balance disponible
        self.available_balance_var = tk.StringVar(value="")
        ttk.Label(from_frame, textvariable=self.available_balance_var, font=("Arial", 9), foreground="gray").pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(from_frame, text="Quantité:").pack(side=tk.LEFT, padx=(20, 5))
        self.amount_var = tk.StringVar(value="1.0")
        amount_entry = ttk.Entry(from_frame, textvariable=self.amount_var, width=15)
        amount_entry.pack(side=tk.LEFT, padx=5)
        amount_entry.bind('<KeyRelease>', self.update_conversion_rate)

        # Deuxième ligne: VERS et résultat
        to_frame = ttk.Frame(conversion_frame)
        to_frame.pack(fill=tk.X, pady=2)

        ttk.Label(to_frame, text="Vers:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.to_asset_var = tk.StringVar()
        self.to_combo = ttk.Combobox(to_frame, textvariable=self.to_asset_var, width=12, state="readonly")
        self.to_combo.pack(side=tk.LEFT, padx=5)
        self.to_combo.bind('<<ComboboxSelected>>', self.update_conversion_rate)

        ttk.Label(to_frame, textvariable=self.conversion_rate_var, font=("Arial", 10)).pack(side=tk.LEFT, padx=(20, 5))

        # Troisième ligne: boutons et résultat
        action_frame = ttk.Frame(conversion_frame)
        action_frame.pack(fill=tk.X, pady=5)

        ttk.Button(action_frame, text="🔄 Convertir", command=self.execute_conversion).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="💱 Inverser", command=self.swap_assets).pack(side=tk.LEFT, padx=5)
        ttk.Label(action_frame, textvariable=self.conversion_result_var, font=("Arial", 10)).pack(side=tk.LEFT, padx=(20, 5))

        # Quatrième ligne: affichage des frais
        fees_frame = ttk.Frame(conversion_frame)
        fees_frame.pack(fill=tk.X, pady=2)
        ttk.Label(fees_frame, textvariable=self.conversion_fees_var, font=("Arial", 9), foreground="orange").pack(side=tk.LEFT, padx=5)

        # Balances
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
                self.pnl_tracker = PnLTracker(self.trader)
                self.populate_asset_combos()
                self.test_connection()
            except Exception as e:
                logger.error(f"Erreur init: {e}")
                messagebox.showerror("Erreur", f"Erreur de configuration: {e}")

    def populate_asset_combos(self):
        if self.trader:
            try:
                # Pour "Vers" : tous les actifs disponibles sur Binance
                all_assets = self.trader.get_all_tradeable_assets()
                popular_assets = ['BTC', 'ETH', 'USDT', 'USDC', 'BNB', 'BUSD', 'ADA', 'DOT', 'MATIC', 'AVAX']

                # Trier tous les actifs avec les populaires en premier
                sorted_all_assets = []
                for asset in popular_assets:
                    if asset in all_assets:
                        sorted_all_assets.append(asset)

                remaining_assets = [a for a in all_assets if a not in popular_assets]
                sorted_all_assets.extend(sorted(remaining_assets))

                # La combobox "Vers" contient tous les actifs Binance
                self.to_combo['values'] = sorted_all_assets

                # Pour "De" : seulement les actifs en portefeuille (sera mis à jour dans update_owned_assets)
                self.update_owned_assets()

                # Valeurs par défaut
                if 'USDT' in sorted_all_assets:
                    self.to_asset_var.set('USDT')

            except Exception as e:
                logger.error(f"Erreur chargement actifs: {e}")

    def update_owned_assets(self):
        """Met à jour la combobox 'De' avec seulement les actifs possédés"""
        if not self.trader or not self.all_balances:
            self.from_combo['values'] = []
            return

        try:
            # Récupérer les actifs possédés avec une balance > 0
            owned_assets = list(self.all_balances.keys())

            # Trier par valeur USD décroissante pour mettre les plus gros en premier
            owned_assets.sort(key=lambda x: self.all_balances[x]['usd_value'], reverse=True)

            self.from_combo['values'] = owned_assets

            # Si l'actif actuellement sélectionné n'est plus disponible, sélectionner le premier
            current_from = self.from_asset_var.get()
            if current_from not in owned_assets and owned_assets:
                self.from_asset_var.set(owned_assets[0])
                self.update_conversion_rate()

        except Exception as e:
            logger.error(f"Erreur mise à jour actifs possédés: {e}")

    def update_conversion_rate(self, event=None):
        if not self.trader:
            return

        try:
            from_asset = self.from_asset_var.get()
            to_asset = self.to_asset_var.get()
            amount_str = self.amount_var.get()

            # Mettre à jour l'affichage de la balance disponible
            if from_asset and from_asset in self.all_balances:
                available = self.all_balances[from_asset]['free']
                self.available_balance_var.set(f"Dispo: {available:.6f}")
            else:
                self.available_balance_var.set("")

            if not from_asset or not to_asset or not amount_str:
                self.conversion_rate_var.set("Taux: --")
                return

            amount = float(amount_str)
            if amount <= 0:
                self.conversion_rate_var.set("Taux: --")
                return

            result = self.trader.get_conversion_rate(from_asset, to_asset, amount)

            if result is not None:
                self.conversion_rate_var.set(f"≈ {result:.8f} {to_asset}")
            else:
                self.conversion_rate_var.set("Conversion impossible")

        except ValueError:
            self.conversion_rate_var.set("Quantité invalide")
        except Exception as e:
            logger.error(f"Erreur calcul taux: {e}")
            self.conversion_rate_var.set("Erreur")

    def swap_assets(self):
        from_asset = self.from_asset_var.get()
        to_asset = self.to_asset_var.get()

        self.from_asset_var.set(to_asset)
        self.to_asset_var.set(from_asset)
        self.update_conversion_rate()

    def execute_conversion(self):
        if not self.trader:
            messagebox.showerror("Erreur", "Pas de connexion Binance")
            return

        try:
            from_asset = self.from_asset_var.get()
            to_asset = self.to_asset_var.get()
            amount_str = self.amount_var.get()

            if not from_asset or not to_asset or not amount_str:
                messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
                return

            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Erreur", "Quantité doit être positive")
                return

            # Vérifier que l'utilisateur a suffisamment de balance
            if from_asset not in self.all_balances:
                messagebox.showerror("Erreur", f"Vous n'avez pas de {from_asset} dans votre portefeuille")
                return

            available = self.all_balances[from_asset]['free']
            if available <= 0:
                messagebox.showerror("Erreur", f"Aucune balance libre disponible pour {from_asset}")
                return

            if amount > available:
                messagebox.showerror("Erreur", f"Quantité insuffisante. Disponible: {available:.8f} {from_asset}")
                return

            # Confirmer la conversion
            estimated = self.trader.get_conversion_rate(from_asset, to_asset, amount)
            if estimated is None:
                messagebox.showerror("Erreur", "Impossible de calculer le taux de conversion")
                return

            confirm_msg = f"Convertir {amount} {from_asset} vers ≈ {estimated:.8f} {to_asset}?"
            if not messagebox.askyesno("Confirmation", confirm_msg):
                return

            # Exécuter la conversion
            def do_conversion():
                try:
                    result = self.trader.convert_asset(from_asset, to_asset, amount)
                    if result:
                        # Afficher le résultat selon le type de conversion
                        if result.get('type') == 'triangular':
                            self.conversion_result_var.set(f"✅ Conversion réussie (via {result['intermediate']})")
                        else:
                            self.conversion_result_var.set("✅ Conversion réussie")

                        # Afficher les frais
                        total_fee_usdt = result.get('total_fee_usdt', 0)
                        if total_fee_usdt > 0:
                            if result.get('type') == 'triangular':
                                # Pour les conversions triangulaires, afficher plus de détails
                                combined_fees = result.get('combined_fees', {})
                                fees_text = ", ".join([f"{amount:.6f} {asset}" for asset, amount in combined_fees.items()])
                                self.conversion_fees_var.set(f"💸 Frais: {fees_text} (≈ ${total_fee_usdt:.4f})")
                            else:
                                # Pour les conversions directes
                                fees = result.get('fees', {}).get('total_fees', {})
                                if fees:
                                    fees_text = ", ".join([f"{amount:.6f} {asset}" for asset, amount in fees.items()])
                                    self.conversion_fees_var.set(f"💸 Frais: {fees_text} (≈ ${total_fee_usdt:.4f})")
                                else:
                                    self.conversion_fees_var.set(f"💸 Frais: ≈ ${total_fee_usdt:.4f}")
                        else:
                            self.conversion_fees_var.set("💸 Frais: Calcul en cours...")

                        # Actualiser les balances
                        self.root.after(1000, self.refresh_balances)
                    else:
                        self.conversion_result_var.set("❌ Échec de la conversion")
                        self.conversion_fees_var.set("")

                except Exception as e:
                    logger.error(f"Erreur conversion: {e}")
                    self.conversion_result_var.set(f"❌ Erreur: {e}")
                    self.conversion_fees_var.set("")

            threading.Thread(target=do_conversion, daemon=True).start()
            self.conversion_result_var.set("⏳ Conversion en cours...")

        except ValueError:
            messagebox.showerror("Erreur", "Quantité invalide")
        except Exception as e:
            logger.error(f"Erreur exécution conversion: {e}")
            messagebox.showerror("Erreur", f"Erreur: {e}")

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

        # Mettre à jour la combobox "De" avec les actifs possédés
        self.update_owned_assets()

    def execute_rebalancing(self):
        if not self.portfolio_manager or not self.all_balances:
            messagebox.showerror("Erreur", "Données non disponibles")
            return

        try:
            # Mettre à jour la config
            self.portfolio_config = {
                'btc_percent': float(self.btc_var.get()),
                'usdc_percent': float(self.usdc_var.get()),
                'altcoin_percent': float(self.alt_var.get())
            }
            
            if sum(self.portfolio_config.values()) != 100:
                messagebox.showerror("Erreur", "La somme doit être 100%")
                return

            plan = self.portfolio_manager.calculate_rebalancing_plan(self.all_balances, self.portfolio_config)
            
            if not plan.get('actions'):
                messagebox.showinfo("Info", "✅ Portfolio déjà équilibré!")
                return

            # Confirmation
            actions_text = "\n".join([
                f"• {a['action']} {a['asset']}: ${a['usd_amount']:.2f}"
                for a in plan['actions'][:5]
            ])
            
            if not messagebox.askyesno("Confirmation", f"Exécuter ces actions?\n\n{actions_text}"):
                return

            self._execute_plan(plan)

        except ValueError:
            messagebox.showerror("Erreur", "Pourcentages invalides")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {e}")

    def _execute_plan(self, plan):
        def execute():
            success, failed = 0, 0
            total_rebalancing_fees_usdt = 0
            detailed_fees = {}

            for action in plan['actions']:
                asset, action_type, usd_amount = action['asset'], action['action'], action['usd_amount']

                # Ignorer actions incohérentes et petits montants
                if usd_amount < 10:
                    continue

                # Éviter les conversions inutiles entre stablecoins
                stablecoins = {'USDC', 'USDT', 'BUSD', 'FDUSD'}
                if action_type == "VENDRE" and asset in stablecoins:
                    continue

                try:
                    result = None
                    if action_type == "VENDRE" and asset in self.all_balances:
                        bal = self.all_balances[asset]
                        qty = bal['balance'] * (usd_amount / bal['usd_value'])
                        target = 'USDC' if 'USDC' in self.all_balances else 'USDT'
                        result = self.trader.convert_asset(asset, target, qty)

                    elif action_type == "ACHETER":
                        source = 'USDC' if 'USDC' in self.all_balances else 'USDT'
                        if source in self.all_balances:
                            result = self.trader.convert_asset(source, asset, round(usd_amount, 2))

                    # Ajouter les frais de cette conversion au total
                    if result and isinstance(result, dict):
                        conversion_fee_usdt = result.get('total_fee_usdt', 0)
                        total_rebalancing_fees_usdt += conversion_fee_usdt

                        # Accumuler les frais détaillés par actif
                        if result.get('type') == 'triangular':
                            combined_fees = result.get('combined_fees', {})
                            for fee_asset, fee_amount in combined_fees.items():
                                detailed_fees[fee_asset] = detailed_fees.get(fee_asset, 0) + fee_amount
                        else:
                            fees = result.get('fees', {}).get('total_fees', {})
                            for fee_asset, fee_amount in fees.items():
                                detailed_fees[fee_asset] = detailed_fees.get(fee_asset, 0) + fee_amount

                    success += 1
                    time.sleep(0.5)  # Délai entre ordres

                except Exception as e:
                    failed += 1
                    logger.error(f"Erreur {action_type} {asset}: {e}")

            # Actualiser et afficher résultat avec frais
            self.root.after(0, self.refresh_balances)

            # Préparer le message avec les frais
            fees_details = ""
            if detailed_fees:
                fees_list = [f"{amount:.6f} {asset}" for asset, amount in detailed_fees.items()]
                fees_details = f"\n\n💸 Frais totaux du rééquilibrage:\n{', '.join(fees_list)}\n≈ ${total_rebalancing_fees_usdt:.4f}"

            msg = f"✅ Rééquilibrage terminé!\n\nRéussies: {success}\nÉchouées: {failed}{fees_details}"
            self.root.after(0, lambda: messagebox.showinfo("Résultat", msg))

            # Logger les frais pour référence
            if total_rebalancing_fees_usdt > 0:
                logger.info(f"Coût total du rééquilibrage: ${total_rebalancing_fees_usdt:.4f} en frais")

        threading.Thread(target=execute, daemon=True).start()

    def refresh_pnl(self):
        """Actualise le calcul du P&L pour toutes les périodes"""
        if not self.pnl_tracker:
            messagebox.showerror("Erreur", "P&L Tracker non initialisé")
            return

        def calculate_pnl():
            try:
                # Réinitialiser les affichages
                self.pnl_7d_var.set("7j: ⏳ Calcul...")
                self.pnl_30d_var.set("30j: ⏳ Calcul...")
                self.pnl_365d_var.set("365j: ⏳ Calcul...")

                # Calculer les P&L
                pnl_results = self.pnl_tracker.calculate_pnl_periods()

                # Mettre à jour l'affichage
                def update_display():
                    for period in ['7d', '30d', '365d']:
                        if period in pnl_results:
                            data = pnl_results[period]
                            absolute = data['absolute']
                            trade_count = data.get('trade_count', 0)
                            total_fees = data.get('total_fees', 0)

                            # Formater avec couleurs (simulées avec emojis)
                            if absolute > 0:
                                emoji = "📈"
                                color_text = f"{emoji} +${absolute:.2f}"
                            elif absolute < 0:
                                emoji = "📉"
                                color_text = f"{emoji} ${absolute:.2f}"
                            else:
                                emoji = "➡️"
                                color_text = f"{emoji} $0.00"

                            # Ajouter info sur trades et frais
                            if trade_count > 0:
                                color_text += f" ({trade_count} trades, ${total_fees:.2f} frais)"

                            # Mettre à jour la variable correspondante
                            period_display = period.replace('d', 'j')
                            if period == '7d':
                                self.pnl_7d_var.set(f"{period_display}: {color_text}")
                            elif period == '30d':
                                self.pnl_30d_var.set(f"{period_display}: {color_text}")
                            elif period == '365d':
                                self.pnl_365d_var.set(f"{period_display}: {color_text}")
                        else:
                            # En cas d'erreur pour une période
                            period_display = period.replace('d', 'j')
                            if period == '7d':
                                self.pnl_7d_var.set(f"{period_display}: ❌ Erreur")
                            elif period == '30d':
                                self.pnl_30d_var.set(f"{period_display}: ❌ Erreur")
                            elif period == '365d':
                                self.pnl_365d_var.set(f"{period_display}: ❌ Erreur")

                self.root.after(0, update_display)

            except Exception as e:
                logger.error(f"Erreur calcul P&L: {e}")
                def show_error():
                    self.pnl_7d_var.set("7j: ❌ Erreur")
                    self.pnl_30d_var.set("30j: ❌ Erreur")
                    self.pnl_365d_var.set("365j: ❌ Erreur")
                    messagebox.showerror("Erreur P&L", f"Erreur calcul P&L: {e}")
                self.root.after(0, show_error)

        threading.Thread(target=calculate_pnl, daemon=True).start()

    def debug_pnl(self):
        """Lance le debug P&L dans la console"""
        if not self.pnl_tracker:
            messagebox.showerror("Erreur", "P&L Tracker non initialisé")
            return

        def run_debug():
            try:
                print("\n" + "="*50)
                print("DEBUG P&L - Lancement...")
                self.pnl_tracker.debug_pnl_calculation(7)
                self.pnl_tracker.debug_pnl_calculation(30)
                print("="*50)
            except Exception as e:
                print(f"Erreur debug: {e}")

        threading.Thread(target=run_debug, daemon=True).start()
        messagebox.showinfo("Debug", "Debug P&L lancé - Voir la console pour les détails")

def main():
    root = tk.Tk()
    app = TradingApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: root.destroy() if messagebox.askokcancel("Quitter", "Fermer l'application?") else None)
    root.mainloop()

if __name__ == "__main__":
    main()
