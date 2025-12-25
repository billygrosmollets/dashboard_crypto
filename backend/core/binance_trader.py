#!/usr/bin/env python3
"""
Binance Trader - Core trading logic extracted from main.py
PRESERVED: Original business logic without modifications
"""
import logging
from binance.client import Client

logger = logging.getLogger(__name__)


class BinanceTrader:
    def __init__(self, api_key, api_secret, testnet=False):
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.all_symbols = []
        self.all_assets = set()
        self.exchange_info = None
        logger.info(f"Client Binance initialisÃ© (testnet: {testnet})")
        self._load_exchange_info()

    def _load_exchange_info(self):
        try:
            self.exchange_info = self.client.get_exchange_info()
            self.all_symbols = [s['symbol'] for s in self.exchange_info['symbols'] if s['status'] == 'TRADING']
            for symbol_info in self.exchange_info['symbols']:
                if symbol_info['status'] == 'TRADING':
                    self.all_assets.add(symbol_info['baseAsset'])
                    self.all_assets.add(symbol_info['quoteAsset'])
            logger.info(f"ChargÃ© {len(self.all_symbols)} paires et {len(self.all_assets)} actifs")
        except Exception as e:
            logger.error(f"Erreur chargement exchange info: {e}")

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
                    'balance': total,
                    'usd_value': usd_val
                }
        return balances
