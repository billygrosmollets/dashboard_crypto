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
        # Configuration par token - sera mise à jour dynamiquement
        self.token_allocations = {}
        self.allocation_entries = {}  # Stockage des widgets d'entrée

    def create_config_ui(self, parent, callback_refresh_balances, callback_add_fee=None):
        """Crée l'interface de configuration du portfolio par token"""
        self.callback_refresh_balances = callback_refresh_balances
        self.callback_add_fee = callback_add_fee

        config_frame = ttk.LabelFrame(parent, text="⚖️ Rééquilibrage par Token", padding="10")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Section header avec boutons
        header_frame = ttk.Frame(config_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Allocation du Portfolio par Token",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        ttk.Button(header_frame, text="⚡ Rééquilibrer",
                  command=self.execute_rebalancing).pack(side=tk.RIGHT)

        # Zone scrollable pour les tokens
        canvas = tk.Canvas(config_frame, height=300)
        scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Info total en bas
        self.total_allocation_var = tk.StringVar(value="Total: 0%")
        ttk.Label(config_frame, textvariable=self.total_allocation_var,
                 font=("Arial", 11, "bold"), foreground="blue").pack(pady=5)

        # Initialiser avec les tokens du portfolio
        self.refresh_tokens()

        return config_frame

    def refresh_tokens(self):
        """Actualise la liste des tokens avec leurs allocations"""
        try:
            # Récupérer les balances actuelles
            balances = self.trader.get_all_balances_usd(5.0)  # Min 5$ pour éviter la poussière

            # Vider la frame scrollable
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            self.allocation_entries.clear()

            # Créer l'en-tête simplifié
            ttk.Label(self.scrollable_frame, text="Token", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=20, pady=5, sticky="w")
            ttk.Label(self.scrollable_frame, text="% Target", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=20, pady=5)

            total_value = sum(data['usd_value'] for data in balances.values())

            if total_value == 0:
                ttk.Label(self.scrollable_frame, text="Aucun token trouvé",
                         font=("Arial", 10)).grid(row=1, column=0, columnspan=2, padx=20, pady=10)
                return

            # Trier les tokens par nom pour avoir un ordre stable
            sorted_tokens = sorted(balances.items(), key=lambda x: x[0])

            row = 1
            for token, data in sorted_tokens:
                current_percent = (data['usd_value'] / total_value) * 100

                # Nom du token
                ttk.Label(self.scrollable_frame, text=token, font=("Arial", 10, "bold")).grid(row=row, column=0, padx=20, pady=2, sticky="w")

                # % target (entrée modifiable) - on garde la valeur actuelle si déjà définie
                if token in self.allocation_entries:
                    # Garder la valeur existante
                    target_var = self.allocation_entries[token]
                else:
                    # Nouvelle entrée avec le pourcentage actuel
                    target_var = tk.StringVar(value=str(round(current_percent, 1)))
                    self.allocation_entries[token] = target_var

                target_entry = ttk.Entry(self.scrollable_frame, textvariable=target_var, width=10)
                target_entry.grid(row=row, column=1, padx=20, pady=2)
                target_entry.bind('<KeyRelease>', self.on_allocation_change)

                row += 1


            self.update_total_allocation()

        except Exception as e:
            logger.error(f"Erreur refresh tokens: {e}")

    def on_allocation_change(self, event=None):
        """Callback quand une allocation change"""
        self.update_total_allocation()

    def update_total_allocation(self):
        """Met à jour l'affichage du total des allocations"""
        try:
            total = 0
            for var in self.allocation_entries.values():
                try:
                    value = float(var.get())
                    total += value
                except ValueError:
                    pass

            # Colorier selon si c'est correct
            if abs(total - 100) < 0.1:
                color = "green"
                status = "✅"
            elif total > 100:
                color = "red"
                status = "⚠️"
            else:
                color = "orange"
                status = "⚡"

            self.total_allocation_var.set(f"{status} Total: {total:.1f}%")

        except Exception as e:
            logger.error(f"Erreur update total: {e}")


    def execute_rebalancing(self):
        """Exécute le rééquilibrage du portfolio basé sur les allocations par token"""
        if not self.portfolio_manager:
            messagebox.showerror("Erreur", "Portfolio manager non disponible")
            return

        try:
            # Vérifier que le total fait 100%
            total_allocation = 0
            target_allocations = {}

            for token, var in self.allocation_entries.items():
                try:
                    percent = float(var.get())
                    total_allocation += percent
                    target_allocations[token] = percent
                except ValueError:
                    messagebox.showerror("Erreur", f"Pourcentage invalide pour {token}")
                    return

            if abs(total_allocation - 100) > 0.1:
                messagebox.showerror("Erreur", f"Total des allocations: {total_allocation:.1f}% (doit être 100%)")
                return

            # Actualiser les balances juste avant le rééquilibrage pour avoir les données fraîches
            all_balances = self.trader.get_all_balances_usd(5.0)
            total_value = sum(b['usd_value'] for b in all_balances.values())

            if total_value == 0:
                messagebox.showerror("Erreur", "Portfolio vide")
                return

            # Calculer le plan de rééquilibrage basé sur les tokens individuels
            plan = self.calculate_token_rebalance_plan(all_balances, total_value, target_allocations)

            if not plan['actions']:
                messagebox.showinfo("Info", "✅ Portfolio déjà équilibré selon vos allocations !")
                return

            # Afficher le plan
            actions_text = "\n".join([
                f"• {action['action']} {action['asset']}: ${action['usd_amount']:.2f}"
                for action in plan['actions'][:8]  # Limiter l'affichage
            ])

            if len(plan['actions']) > 8:
                actions_text += f"\n... et {len(plan['actions']) - 8} autres actions"

            if not messagebox.askyesno("Confirmation", f"Exécuter ces actions?\n\n{actions_text}"):
                return

            self._execute_plan(plan, self.callback_refresh_balances, self.callback_add_fee)

        except Exception as e:
            logger.error(f"Erreur rééquilibrage: {e}")
            messagebox.showerror("Erreur", f"Erreur: {e}")

    def calculate_token_rebalance_plan(self, all_balances, total_value, target_allocations):
        """Calcule le plan de rééquilibrage basé sur les allocations individuelles par token"""
        plan = {'actions': [], 'current_allocation': {}, 'target_allocation': {}}

        # Calculer les valeurs cibles
        target_values = {}
        for token, percent in target_allocations.items():
            target_values[token] = (percent / 100) * total_value

        # Analyser chaque token
        for token, target_value in target_values.items():
            current_value = all_balances.get(token, {'usd_value': 0})['usd_value']
            difference = target_value - current_value

            # Seuil minimum pour éviter les micro-ajustements
            if abs(difference) > total_value * 0.005:  # 0.5% du portfolio total
                if difference > 0:
                    # Besoin d'acheter ce token
                    plan['actions'].append({
                        'asset': token,
                        'action': 'ACHETER',
                        'usd_amount': difference,
                        'priority': 1
                    })
                else:
                    # Besoin de vendre ce token
                    plan['actions'].append({
                        'asset': token,
                        'action': 'VENDRE',
                        'usd_amount': abs(difference),
                        'priority': 1
                    })

            plan['current_allocation'][token] = current_value
            plan['target_allocation'][token] = target_value

        # Trier par importance (montant décroissant)
        plan['actions'].sort(key=lambda x: x['usd_amount'], reverse=True)

        return plan

    def _execute_plan(self, plan, callback_refresh_balances=None, callback_add_fee=None):
        """Exécute le plan de rééquilibrage"""
        def execute():
            success, failed = 0, 0
            total_rebalancing_fees_usdt = 0
            detailed_fees = {}

            all_balances = self.trader.get_all_balances_usd(5.0)

            for action in plan['actions']:
                asset, action_type, usd_amount = action['asset'], action['action'], action['usd_amount']


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

            # Créer un résumé détaillé avec les frais
            volume_total = sum(action['usd_amount'] for action in plan['actions'])

            msg = f"✅ Rééquilibrage terminé!\n\n"
            msg += f"📊 Actions: {success} réussies, {failed} échouées\n"
            msg += f"💰 Volume total: ${volume_total:.2f}\n"
            msg += f"💸 Frais totaux: ${total_rebalancing_fees_usdt:.4f}"

            if total_rebalancing_fees_usdt > 0 and volume_total > 0:
                fee_percentage = (total_rebalancing_fees_usdt / volume_total) * 100
                msg += f" ({fee_percentage:.3f}%)"

            messagebox.showinfo("Résumé Rééquilibrage", msg)

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
        self.available_balance_var = tk.StringVar(value="")

    def create_converter_ui(self, parent, all_balances_ref, update_owned_assets_callback, callback_add_fee=None):
        """Crée l'interface du convertisseur crypto"""
        self.all_balances_ref = all_balances_ref
        self.update_owned_assets_callback = update_owned_assets_callback
        self.callback_add_fee = callback_add_fee

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

                        # Ajouter les frais à l'historique
                        total_fee_usdt = result.get('total_fee_usdt', 0)
                        if total_fee_usdt > 0 and self.callback_add_fee:
                            conversion_amount = float(self.amount_var.get()) if self.amount_var.get() else 0
                            self.callback_add_fee(f"Conversion {from_asset}→{to_asset}", conversion_amount, total_fee_usdt)

                        # Actualiser les balances
                        if self.update_owned_assets_callback:
                            self.update_owned_assets_callback()
                    else:
                        self.conversion_result_var.set("❌ Échec de la conversion")

                except Exception as e:
                    logger.error(f"Erreur conversion: {e}")
                    self.conversion_result_var.set(f"❌ Erreur: {e}")

            threading.Thread(target=do_conversion, daemon=True).start()
            self.conversion_result_var.set("⏳ Conversion en cours...")

        except ValueError:
            messagebox.showerror("Erreur", "Quantité invalide")
        except Exception as e:
            logger.error(f"Erreur exécution conversion: {e}")
            messagebox.showerror("Erreur", f"Erreur: {e}")