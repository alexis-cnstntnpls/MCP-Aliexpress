# MCP-AliExpress (France)

Serveur MCP (Model Context Protocol) optimisé pour **AliExpress France** avec prix en euros (€) et livraison en France métropolitaine.

Permet à Claude Desktop, Cursor et aux agents personnalisés ChatGPT (Custom GPTs) d'effectuer des recherches de produits, de consulter les détails d'articles et d'analyser les évaluations et avis réels d'acheteurs.

---

## Fonctionnalités

1. **`search_aliexpress_products`** :
   - Recherche par mots-clés en français.
   - Tri par pertinence (`default`), prix croissant (`price_asc`), prix décroissant (`price_desc`) ou meilleures ventes (`orders`).
   - Filtre par budget minimum / maximum (`min_price`, `max_price`).
   - Filtre livraison gratuite (`free_shipping=True`).
   - Données retournées : ID, titre, prix formaté, prix numérique EUR, prix d'origine, remise, volume des ventes (ex: `+ 50 000 vendus`), note sur 5, badges d'expédition, pays d'expédition (`FR`, `ES`, `CN`), liste des photos et lien produit direct.

2. **`get_aliexpress_product_details`** :
   - Récupération des informations d'un produit via son ID ou son URL complète.
   - Titre intégral, prix, note moyenne, volume de ventes, badges d'expédition et galerie d'images haute résolution.

3. **`get_aliexpress_product_reviews`** :
   - Avis clients authentiques et vérifiés avec pagination (`page`, `page_size`).
   - Note globale et taux de satisfaction positif (`98.5%`).
   - Décomposition des notes (5 étoiles, 4 étoiles, 3 étoiles, etc.).
   - Détail par avis : pays de l'acheteur (ex: `FR`, `BE`), note sur 5, date, commentaire textuel, variante/SKU achetée, mode de livraison et photos réelles postées par les clients.
   - Filtre par acheteurs locaux / français (`filter_type="local"`) ou avec photos (`filter_type="image"`).

4. **Robustesse et contournement anti-bot** :
   - Utilise `curl_cffi` avec émulation d'empreinte TLS/JA3/JA4 Chrome 124+.
   - Injecte automatiquement le cookie de localisation `aep_usuc_f` (France / EUR).
   - Queue de requêtes sérialisée avec temporisation humaine aléatoire pour éviter le blocage par burst de requêtes.

---

## Installation locale

```bash
git clone https://github.com/votre-user/MCP-AliExpress.git && cd MCP-AliExpress && python3 -m venv .venv && .venv/bin/pip install -e .
```

---

## Lancement

### Mode stdio (Claude Desktop / Cursor)

```bash
/home/alexis/MCP-AliExpress/.venv/bin/aliexpress-mcp --transport stdio
```

### Mode HTTP / SSE (Agent distant / ChatGPT)

```bash
/home/alexis/MCP-AliExpress/.venv/bin/aliexpress-mcp --transport sse --host 0.0.0.0 --port 8001
```

---

## Configuration Claude Desktop

Ajoutez dans votre fichier `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "aliexpress-fr": {
      "command": "/home/alexis/MCP-AliExpress/.venv/bin/aliexpress-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

---

## Tests locaux

Pour tester le scraper et le protocole MCP en local :

```bash
/home/alexis/MCP-AliExpress/.venv/bin/python /home/alexis/MCP-AliExpress/tests/test_scraper.py
```

```bash
/home/alexis/MCP-AliExpress/.venv/bin/python /home/alexis/MCP-AliExpress/tests/test_server_mcp.py
```
