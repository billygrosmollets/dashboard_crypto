# 🚀 Guide de Déploiement - Crypto Portfolio Dashboard

Guide complet pour déployer l'application en production avec Docker.

---

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Configuration PC Local (Windows)](#configuration-pc-local-windows)
3. [Déploiement Local](#déploiement-local)
4. [Accès à l'Application](#accès-à-lapplication)
5. [Maintenance et Monitoring](#maintenance-et-monitoring)
6. [Migration VPS (Optionnel)](#migration-vps-optionnel)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Prérequis

### Logiciels Requis

- **Docker Desktop pour Windows** (version 20.10+)
  - Téléchargement : https://www.docker.com/products/docker-desktop
  - Inclut Docker Engine + Docker Compose

### Credentials Binance

Vous aurez besoin de :
- Clé API Binance (`BINANCE_API_KEY`)
- Secret API Binance (`BINANCE_API_SECRET`)

**Comment obtenir vos clés** :
1. Connectez-vous à Binance
2. Allez dans **Account → API Management**
3. Créez une nouvelle API Key
4. **Important** : Activez seulement les permissions **READ** (pas de trading/withdraw)

---

## 💻 Configuration PC Local (Windows)

### Étape 1 : Installer Docker Desktop

1. Téléchargez Docker Desktop : https://www.docker.com/products/docker-desktop
2. Exécutez l'installateur
3. Redémarrez votre PC
4. Vérifiez l'installation :

```powershell
docker --version
docker-compose --version
```

Vous devriez voir les versions de Docker affichées.

### Étape 2 : Désactiver la Mise en Veille (CRITIQUE)

⚠️ **TRÈS IMPORTANT** : Si vous fermez l'écran de votre PC portable sans désactiver la mise en veille, l'application s'arrêtera !

**Configuration Windows** :

1. **Paramètres → Système → Alimentation**

2. **"Alimentation et mise en veille"**
   - Écran : `Jamais` (ou 10 min si vous préférez)
   - Mise en veille : `Jamais`

3. **"Paramètres d'alimentation supplémentaires"**
   - Cliquez sur votre mode actuel (Équilibré/Performances)
   - "Modifier les paramètres avancés du mode"
   - **"Mise en veille" → "Autoriser la mise en veille" → "Jamais"**
   - **"Boutons d'alimentation et capot" → "Action de fermeture du capot"**
     - Sur secteur : `Ne rien faire`
     - Sur batterie : `Ne rien faire`
   - Appliquer et OK

✅ Maintenant vous pouvez fermer l'écran sans que l'app s'arrête !

---

## 🎯 Déploiement Local

### Étape 1 : Préparer la Configuration

1. **Ouvrez PowerShell** dans le dossier du projet :

```powershell
cd C:\Users\billy\Documents\dashboard_crypto
```

2. **Créez votre fichier .env** :

```powershell
copy .env.example .env
notepad .env
```

3. **Éditez .env** avec vos vraies valeurs :

```env
# Binance API Credentials
BINANCE_API_KEY=votre_vraie_clé_api_ici
BINANCE_API_SECRET=votre_vrai_secret_ici
BINANCE_TESTNET=False

# Backend Configuration
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=GenerezUneCleSecureAleatoire32Caracteres

# CORS Configuration
# Pour PC local : http://localhost
# Pour accès réseau local : http://localhost,http://192.168.1.42 (votre IP)
ALLOWED_ORIGINS=http://localhost

# Database (ne pas modifier)
DATABASE_URL=sqlite:////app/data/portfolio.db

# Auto-refresh Configuration
AUTO_REFRESH_INTERVAL=60
SNAPSHOT_INTERVAL=60
```

**⚠️ Important** : Ne committez JAMAIS le fichier `.env` sur Git !

### Étape 2 : Déployer avec le Script

```powershell
.\deploy.ps1
```

Le script va :
1. ✅ Vérifier que Docker est lancé
2. 🏗️  Builder les images Docker
3. 🛑 Arrêter les anciens conteneurs
4. 🚀 Démarrer les nouveaux conteneurs
5. 📊 Afficher l'URL d'accès

**Temps de déploiement** : ~5-10 minutes la première fois (téléchargement des images)

### Étape 3 : Vérifier le Déploiement

```powershell
# Voir les conteneurs en cours d'exécution
docker-compose ps

# Voir les logs
docker-compose logs -f
```

Vous devriez voir :
- ✅ `portfolio-backend` - Running
- ✅ `portfolio-frontend` - Running

---

## 🌐 Accès à l'Application

### Depuis le Même PC

Ouvrez votre navigateur : **http://localhost**

### Depuis un Autre Appareil (Téléphone, Tablette, etc.)

1. **Trouvez votre IP locale** :

```powershell
ipconfig
```

Cherchez **"Carte réseau sans fil Wi-Fi" → "Adresse IPv4"**
Exemple : `192.168.1.42`

2. **Accédez depuis l'autre appareil** :

Sur le même réseau WiFi : **http://192.168.1.42**

⚠️ **Note** : L'appareil doit être sur le **même réseau WiFi** que votre PC.

---

## 🔧 Maintenance et Monitoring

### Voir les Logs

```powershell
# Logs de tous les services
docker-compose logs -f

# Logs du backend uniquement
docker-compose logs -f backend

# Logs du frontend uniquement
docker-compose logs -f frontend

# Dernières 100 lignes
docker-compose logs --tail=100
```

### Redémarrer l'Application

```powershell
# Redémarrer tout
docker-compose restart

# Redémarrer un service spécifique
docker-compose restart backend
```

### Arrêter l'Application

```powershell
docker-compose down
```

### Mettre à Jour l'Application

```powershell
# Si vous avez modifié du code
git pull  # Si en version control

# Redéployer
.\deploy.ps1
```

### Sauvegarder la Base de Données

La base de données SQLite est dans `./data/portfolio.db`

```powershell
# Créer une sauvegarde
copy data\portfolio.db data\portfolio_backup_$(Get-Date -Format 'yyyyMMdd').db
```

### Voir l'Utilisation des Ressources

```powershell
docker stats
```

---

## ☁️ Migration VPS (Optionnel)

Si plus tard vous voulez migrer vers un VPS Cloud :

### Sur le VPS (Linux)

```bash
# 1. Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. Cloner le projet
git clone https://github.com/votre-repo/dashboard_crypto.git
cd dashboard_crypto

# 3. Créer .env
cp .env.example .env
nano .env  # Éditer avec vos vraies valeurs

# 4. Déployer
docker-compose up -d

# C'est tout ! Même configuration Docker
```

L'app sera accessible sur : **http://votre-ip-vps**

---

## 🐛 Troubleshooting

### Problème : "Docker is not running"

**Solution** :
1. Ouvrez Docker Desktop
2. Attendez qu'il démarre complètement
3. Réessayez

### Problème : "Port 80 is already in use"

**Solution** :
1. Un autre service utilise le port 80 (Skype, IIS, etc.)
2. Modifiez `docker-compose.yml` :

```yaml
frontend:
  ports:
    - "8080:80"  # Change 80 → 8080
```

3. Accédez ensuite à : `http://localhost:8080`

### Problème : "Cannot connect to backend"

**Solution** :
1. Vérifiez les logs backend :

```powershell
docker-compose logs backend
```

2. Vérifiez que le backend est démarré :

```powershell
docker-compose ps
```

3. Testez l'API directement :

```powershell
curl http://localhost/health
```

### Problème : Auto-refresh ne fonctionne pas

**Vérifiez dans les logs** :

```powershell
docker-compose logs backend | Select-String "Auto-refresh"
```

Vous devriez voir : `✅ Auto-refresh service started (production mode)`

### Problème : Erreur "BINANCE_API_KEY not found"

**Solution** :
1. Vérifiez que `.env` existe :

```powershell
cat .env
```

2. Vérifiez que les credentials sont corrects
3. Redémarrez :

```powershell
docker-compose restart backend
```

### Problème : L'app s'arrête quand je ferme l'écran

**Solution** :
Vous n'avez pas désactivé la mise en veille ! Relisez la section **[Configuration PC Local](#étape-2--désactiver-la-mise-en-veille-critique)**

---

## 📊 Architecture Technique

```
┌─────────────────────────────────────┐
│  Navigateur (http://localhost)     │
└──────────────┬──────────────────────┘
               │
       ┌───────▼────────┐
       │   Nginx (80)   │  ← Frontend Container
       │  Vue.js Build  │
       └───────┬────────┘
               │ (Reverse Proxy)
               │
       ┌───────▼────────┐
       │ Flask (5000)   │  ← Backend Container
       │   Gunicorn     │
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │  SQLite DB     │  ← Persistent Volume
       │ (./data/)      │
       └────────────────┘
```

---

## ✅ Checklist de Déploiement

- [ ] Docker Desktop installé et démarré
- [ ] Mise en veille désactivée (si PC portable)
- [ ] Fichier `.env` créé avec vraies credentials
- [ ] Déployé avec `.\deploy.ps1`
- [ ] Vérifié que les 2 conteneurs sont `Running`
- [ ] Accès réussi à `http://localhost`
- [ ] Auto-refresh fonctionne (vérifier les logs)

---

## 📞 Support

Pour des problèmes ou questions :
1. Vérifiez les logs : `docker-compose logs -f`
2. Consultez ce guide de troubleshooting
3. Vérifiez la configuration dans `.env`

---

**Bonne utilisation de votre Crypto Portfolio Dashboard ! 🚀**
