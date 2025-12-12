#!/usr/bin/env python3
"""
Binance Trader - Core trading logic extracted from main.py
PRESERVED: Original business logic without modifications
"""
import logging
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)


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
