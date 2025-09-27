#!/usr/bin/env python3
"""
Configuration Portfolio et Convertisseur Crypto Universal
Module contenant la logique de configuration du portfolio et de conversion crypto
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging

logger = logging.getLogger(__name__)

class PortfolioConfig:
    """Gestionnaire de configuration du portfolio"""

    def __init__(self, trader, portfolio_manager):
        self.trader = trader
        self.portfolio_manager = portfolio_manager
        self.portfolio_config = {'btc_percent': 20, 'usdc_percent': 40, 'altcoin_percent': 40}

    def create_config_ui(self, parent, callback_refresh_balances):
        """Crée l'interface de configuration du portfolio"""
        config_frame = ttk.LabelFrame(parent, text="Configuration Portfolio", padding="10")
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

        ttk.Button(config_frame, text="⚡ Rééquilibrer",
                  command=lambda: self.execute_rebalancing(callback_refresh_balances)).grid(row=0, column=6, padx=20)

        return config_frame

    def execute_rebalancing(self, callback_refresh_balances=None):
        """Exécute le rééquilibrage du portfolio"""
        if not self.portfolio_manager:
            messagebox.showerror("Erreur", "Portfolio manager non disponible")
            return

        try:
            # Récupérer les balances actuelles
            all_balances = self.trader.get_all_balances_usd(5.0)

            # Mettre à jour la config
            self.portfolio_config = {
                'btc_percent': float(self.btc_var.get()),
                'usdc_percent': float(self.usdc_var.get()),
                'altcoin_percent': float(self.alt_var.get())
            }

            if sum(self.portfolio_config.values()) != 100:
                messagebox.showerror("Erreur", "La somme doit être 100%")
                return

            plan = self.portfolio_manager.calculate_rebalancing_plan(all_balances, self.portfolio_config)

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

            self._execute_plan(plan, callback_refresh_balances)

        except ValueError:
            messagebox.showerror("Erreur", "Pourcentages invalides")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {e}")

    def _execute_plan(self, plan, callback_refresh_balances=None):
        """Exécute le plan de rééquilibrage"""
        def execute():
            success, failed = 0, 0
            total_rebalancing_fees_usdt = 0
            detailed_fees = {}

            all_balances = self.trader.get_all_balances_usd(5.0)

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
                    if action_type == "VENDRE" and asset in all_balances:
                        bal = all_balances[asset]
                        qty = bal['balance'] * (usd_amount / bal['usd_value'])
                        target = 'USDC' if 'USDC' in all_balances else 'USDT'
                        result = self.trader.convert_asset(asset, target, qty)

                    elif action_type == "ACHETER":
                        source = 'USDC' if 'USDC' in all_balances else 'USDT'
                        if source in all_balances:
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
                    import time
                    time.sleep(0.5)  # Délai entre ordres

                except Exception as e:
                    failed += 1
                    logger.error(f"Erreur {action_type} {asset}: {e}")

            # Actualiser et afficher résultat avec frais
            if callback_refresh_balances:
                callback_refresh_balances()

            # Préparer le message avec les frais
            fees_details = ""
            if detailed_fees:
                fees_list = [f"{amount:.6f} {asset}" for asset, amount in detailed_fees.items()]
                fees_details = f"\n\n💸 Frais totaux du rééquilibrage:\n{', '.join(fees_list)}\n≈ ${total_rebalancing_fees_usdt:.4f}"

            msg = f"✅ Rééquilibrage terminé!\n\nRéussies: {success}\nÉchouées: {failed}{fees_details}"
            messagebox.showinfo("Résultat", msg)

            # Logger les frais pour référence
            if total_rebalancing_fees_usdt > 0:
                logger.info(f"Coût total du rééquilibrage: ${total_rebalancing_fees_usdt:.4f} en frais")

        threading.Thread(target=execute, daemon=True).start()


class CryptoConverter:
    """Gestionnaire du convertisseur crypto universal"""

    def __init__(self, trader):
        self.trader = trader
        self.conversion_rate_var = tk.StringVar(value="Taux: --")
        self.conversion_result_var = tk.StringVar(value="")
        self.conversion_fees_var = tk.StringVar(value="")
        self.available_balance_var = tk.StringVar(value="")

    def create_converter_ui(self, parent, all_balances_ref, update_owned_assets_callback):
        """Crée l'interface du convertisseur crypto"""
        self.all_balances_ref = all_balances_ref
        self.update_owned_assets_callback = update_owned_assets_callback

        conversion_frame = ttk.LabelFrame(parent, text="🔄 Convertisseur Crypto Universal", padding="10")
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

        # Initialiser les comboboxes
        self.populate_asset_combos()

        return conversion_frame

    def populate_asset_combos(self):
        """Remplit les comboboxes avec les actifs disponibles"""
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
        if not self.trader or not self.all_balances_ref:
            self.from_combo['values'] = []
            return

        try:
            all_balances = self.all_balances_ref()
            # Récupérer les actifs possédés avec une balance > 0
            owned_assets = list(all_balances.keys())

            # Trier par valeur USD décroissante pour mettre les plus gros en premier
            owned_assets.sort(key=lambda x: all_balances[x]['usd_value'], reverse=True)

            self.from_combo['values'] = owned_assets

            # Si l'actif actuellement sélectionné n'est plus disponible, sélectionner le premier
            current_from = self.from_asset_var.get()
            if current_from not in owned_assets and owned_assets:
                self.from_asset_var.set(owned_assets[0])
                self.update_conversion_rate()

        except Exception as e:
            logger.error(f"Erreur mise à jour actifs possédés: {e}")

    def update_conversion_rate(self, event=None):
        """Met à jour le taux de conversion affiché"""
        if not self.trader:
            return

        try:
            from_asset = self.from_asset_var.get()
            to_asset = self.to_asset_var.get()
            amount_str = self.amount_var.get()

            # Mettre à jour l'affichage de la balance disponible
            all_balances = self.all_balances_ref()
            if from_asset and from_asset in all_balances:
                available = all_balances[from_asset]['free']
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
        """Inverse les actifs de conversion"""
        from_asset = self.from_asset_var.get()
        to_asset = self.to_asset_var.get()

        self.from_asset_var.set(to_asset)
        self.to_asset_var.set(from_asset)
        self.update_conversion_rate()

    def execute_conversion(self):
        """Exécute la conversion crypto"""
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
            all_balances = self.all_balances_ref()
            if from_asset not in all_balances:
                messagebox.showerror("Erreur", f"Vous n'avez pas de {from_asset} dans votre portefeuille")
                return

            available = all_balances[from_asset]['free']
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
                        if self.update_owned_assets_callback:
                            self.update_owned_assets_callback()
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