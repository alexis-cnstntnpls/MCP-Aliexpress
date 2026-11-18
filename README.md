# AliExpress FR MCP Server

Serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io) haute performance et résistant aux blocages pour **AliExpress France**, avec prix en euros (€) et livraison en France métropolitaine.

Permet à **Claude Desktop**, **Cursor**, **Cline**, **Claude Code** et aux agents **ChatGPT** d'effectuer des recherches de produits, de consulter les fiches articles détaillées et d'analyser les évaluations et avis réels d'acheteurs.

---

## Sommaire

- [Fonctionnalités clés](#-fonctionnalités-clés)
- [Catalogue des Outils MCP](#-catalogue-des-outils-mcp)
- [Architecture & Résilience Anti-Bot](#-architecture--résilience-anti-bot)
- [Prérequis & Installation](#-prérequis--installation)
- [Modes d'Exécution & Configuration](#-modes-dexécution--configuration)
  - [1. Mode local standard : stdio (Claude Desktop / Cursor)](#1-mode-local-standard--stdio-claude-desktop--cursor)
  - [2. Mode serveur HTTP : Streamable HTTP / SSE (ChatGPT / Accès distant)](#2-mode-serveur-http--streamable-http--sse-chatgpt--accès-distant)
- [Variables d'Environnement](#-variables-denvironnement)
- [Tests & Validation](#-tests--validation)
- [Bibliothèques & Références](#-bibliothèques--références)
- [Licence & Avertissement](#-licence--avertissement)

---

## 🌟 Fonctionnalités clés

1. **Recherche de Produits Optimisée FR :**
   - Mots-clés en français avec extraction des prix réels en euros (€).
   - Tris avancés : pertinence (`default`), prix croissant (`price_asc`), prix décroissant (`price_desc`) ou meilleures ventes (`orders`).
   - Filtre par fourchette de prix (`min_price`, `max_price`) et filtre livraison gratuite (`free_shipping`).
   - Métadonnées complètes : volume des ventes (ex: `+ 50 000 vendus`), note moyenne, pays d'expédition (`FR`, `ES`, `CN`), badges de garantie et liens d'images.

2. **Fiches Produits Exhaustives :**
   - Extraction des informations complètes via ID ou URL produit.
   - Galerie complète d'images haute résolution, remises appliquées et prix d'origine barré.

3. **Avis Clients Authentiques & Vérifiés :**
   - Récupération des évaluations réelles d'acheteurs avec pagination.
   - Taux de satisfaction global (`98.5%`) et décomposition des notes étoiles (1 à 5).
   - Filtres ciblés :
     - `local` : avis d'acheteurs français ou francophones uniquement.
     - `image` : avis contenant des photos réelles du produit reçu par les acheteurs.

4. **Résilience Multi-Canal Anti-Blocage :**
   - Mécanisme de **fallback automatique** : si l'interface Desktop rencontre un seuil de débit ou un défi *punish*, le scraper bascule automatiquement et de façon transparente sur le flux mobile wholesale, assurant une disponibilité ininterrompue.
   - Empreinte TLS/JA3/JA4 Chrome moderne via `curl_cffi`.
   - File d'attente FIFO sérialisée avec temporisation humaine aléatoire.

---

## 🛠 Catalogue des Outils MCP

| Outil | Description | Paramètres principaux |
| :--- | :--- | :--- |
| **`search_aliexpress_products`** | Recherche des articles sur AliExpress France avec filtres de prix, tri et livraison gratuite. | `query` (str, obligatoire), `page` (int, 1-50), `sort` (`default`, `price_asc`, `price_desc`, `orders`), `min_price` (float), `max_price` (float), `free_shipping` (bool). |
| **`get_aliexpress_product_details`** | Récupère la fiche détaillée d'un article : titre complet, galerie photos, prix remisé, prix d'origine et garanties. | `product_id_or_url` (str, ID numérique ou URL complète). |
| **`get_aliexpress_product_reviews`** | Récupère les évaluations et avis authentiques avec notes étoiles, pays de l'acheteur et photos réelles. | `product_id_or_url` (str), `page` (int, 1-50), `page_size` (int, max 20), `filter_type` (`all`, `local`, `image`). |

---

## 🛡 Architecture & Résilience Anti-Bot

AliExpress emploie des protections sophistiquées contre les scrapers basiques. Ce serveur intègre une architecture spécifique :

1. **Émulation TLS / JA3 / JA4 :**
   - Les requêtes utilisent `curl_cffi` pour reproduire à l'identique la signature cryptographique des navigateurs Chrome modernes, empêchant le fingerprinting côté serveur.
2. **Double Canal avec Bascule Automatique (Desktop ⇄ Mobile) :**
   - Canal principal : parsing des flux de données web Desktop.
   - Canal de secours : si un défi de sécurité ou une limitation de débit est détectée, le moteur bascule immédiatement sur le canal mobile wholesale, évitant les erreurs 403 / *punish*.
3. **Cookie de Localisation Préconfiguré :**
   - Injection automatique du cookie `aep_usuc_f` (`site=fra&c_tp=EUR&region=FR&b_locale=fr_FR`) garantissant l'affichage des prix en euros (€) et les délais de livraison métropolitains.
4. **File d'Attente FIFO avec Temporisation Humaine :**
   - Un verrou asynchrone (`REQUEST_QUEUE_LOCK`) sérialise les requêtes et applique un délai pseudo-aléatoire entre 0.4s et 1.0s entre chaque appel pour une signature comportementale naturelle.

---

## 📦 Prérequis & Installation

- **Python :** Version 3.10 ou supérieure.
- **Système d'exploitation :** Linux, macOS ou Windows.

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-compte/MCP-AliExpress.git
cd MCP-AliExpress

# 2. Créer l'environnement virtuel Python
python3 -m venv .venv

# 3. Activer l'environnement virtuel
# Sur Linux / macOS :
source .venv/bin/activate
# Sur Windows :
# .venv\Scripts\activate

# 4. Installer les dépendances en mode éditable
pip install --upgrade pip
pip install -e .
```

---

## 🚀 Modes d'Exécution & Configuration

### 1. Mode local standard : stdio (Claude Desktop / Cursor)

#### Configuration pour Claude Desktop

Ouvrez le fichier de configuration de Claude Desktop :
- **macOS :** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows :** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux :** `~/.config/Claude/claude_desktop_config.json`

Ajoutez la section suivante :

```json
{
  "mcpServers": {
    "aliexpress-fr": {
      "command": "/chemin/absolu/vers/MCP-AliExpress/.venv/bin/aliexpress-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

Redémarrez ensuite Claude Desktop.

#### Configuration pour Claude Code (CLI)

```bash
claude mcp add aliexpress-fr -- /chemin/absolu/vers/MCP-AliExpress/.venv/bin/aliexpress-mcp --transport stdio
```

---

### 2. Mode serveur HTTP : Streamable HTTP / SSE (ChatGPT / Accès distant)

Pour connecter le serveur à **ChatGPT** (menu *Plugins / Serveurs MCP*) ou pour l'héberger sur un serveur distant derrière un reverse-proxy HTTPS :

```bash
python run_http.py
```

Par défaut, le serveur démarre sur `http://127.0.0.1:8001/mcp/aliexpress`.

#### Exemple de service systemd (Linux)

```ini
[Unit]
Description=Serveur MCP AliExpress FR
After=network.target

[Service]
Type=simple
User=votre_utilisateur
WorkingDirectory=/chemin/vers/MCP-AliExpress
Environment="MCP_HOST=127.0.0.1"
Environment="MCP_PORT=8001"
Environment="MCP_PATH=/mcp/aliexpress"
Environment="MCP_PUBLIC_HOST=localhost"
ExecStart=/chemin/vers/MCP-AliExpress/.venv/bin/python /chemin/vers/MCP-AliExpress/run_http.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## ⚙️ Variables d'Environnement

| Variable | Défaut | Description |
| :--- | :--- | :--- |
| `MCP_HOST` | `127.0.0.1` | Adresse IP d'écoute en mode HTTP. |
| `MCP_PORT` | `8001` | Port d'écoute en mode HTTP. |
| `MCP_PATH` | `/mcp/aliexpress` | Préfixe du chemin HTTP pour l'endpoint MCP. |
| `MCP_PUBLIC_HOST` | `localhost` | Nom d'hôte public autorisé pour les reverse-proxies (protection DNS rebinding). |
| `LOG_LEVEL` | `INFO` | Niveau de journalisation (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 🧪 Tests & Validation

Le dépôt inclut une suite de tests unitaires et de stress tests :

```bash
# Tester le scraper (recherche, fiches produits, avis)
python tests/test_scraper.py

# Tester le serveur MCP et l'appel des outils
python tests/test_server_mcp.py

# Exécuter le test d'endurance (validation du basculement anti-blocage)
python tests/stress_test.py
```

---

## 📚 Bibliothèques & Références

Ce projet s'appuie sur les bibliothèques suivantes :

- **[Model Context Protocol SDK (`mcp`)](https://github.com/modelcontextprotocol/python-sdk)** : SDK officiel Anthropic pour l'interopérabilité IA.
- **[curl_cffi](https://github.com/yifeikong/curl_cffi)** : Client HTTP Python avec support de l'émulation TLS et bypass anti-bot.
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** : Analyse syntaxique HTML/XML pour l'extraction de métadonnées.
- **[Pydantic v2](https://github.com/pydantic/pydantic)** : Validation de schémas et modélisation de données typées.
- **[Uvicorn](https://www.uvicorn.org/) & [Starlette](https://www.starlette.io/)** : Moteur ASGI asynchrone pour le transport Streamable HTTP.

---

## ⚖️ Licence & Avertissement

- Publié sous **Licence MIT**.
- **Avertissement :** Ce projet est indépendant et n'est pas affilié à *AliExpress* ou *Alibaba Group*. L'outil doit être utilisé de manière raisonnable, à des fins de consultation personnelle ou de veille tarifaire, dans le respect des conditions générales de la plateforme.
