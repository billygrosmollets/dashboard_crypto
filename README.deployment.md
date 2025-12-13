# 🚀 Quick Start - Déploiement Production

Guide rapide pour déployer l'application avec Docker.

## ⚡ Démarrage Rapide (Windows)

### 1. Installer Docker Desktop
Téléchargez et installez : https://www.docker.com/products/docker-desktop

### 2. Configurer l'Application

```powershell
# Créer votre fichier de configuration
copy .env.example .env
notepad .env  # Éditer avec vos credentials Binance
```

### 3. Déployer

```powershell
.\deploy.ps1
```

### 4. Accéder à l'Application

- **Depuis votre PC** : http://localhost
- **Depuis votre réseau local** : http://192.168.x.x (votre IP locale)

## ⚠️ Important - PC Portable

Si vous utilisez un PC portable, **désactivez la mise en veille** pour que l'app continue de tourner quand vous fermez l'écran :

**Windows** : Paramètres → Système → Alimentation → "Action de fermeture du capot" → **"Ne rien faire"**

## 📚 Documentation Complète

Pour un guide détaillé, consultez : **[DEPLOYMENT.md](./DEPLOYMENT.md)**

Inclut :
- Configuration complète
- Troubleshooting
- Maintenance
- Migration VPS

## 🔧 Commandes Utiles

```powershell
# Voir les logs
docker-compose logs -f

# Redémarrer
docker-compose restart

# Arrêter
docker-compose down

# Mettre à jour
.\deploy.ps1
```

## 📂 Structure

```
dashboard_crypto/
├── backend/              # Flask API
├── frontend/             # Vue.js frontend
├── Dockerfile.backend    # Docker config backend
├── Dockerfile.frontend   # Docker config frontend
├── docker-compose.yml    # Orchestration
├── deploy.ps1           # Script de déploiement
├── .env.example         # Template config
└── DEPLOYMENT.md        # Guide complet
```

## ✅ Checklist

- [ ] Docker Desktop installé
- [ ] `.env` créé avec vos credentials
- [ ] Mise en veille désactivée (PC portable)
- [ ] Déployé avec `.\deploy.ps1`
- [ ] Accessible sur http://localhost

---

**Besoin d'aide ?** Consultez [DEPLOYMENT.md](./DEPLOYMENT.md) pour le guide complet.
