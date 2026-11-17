"""Serveur MCP AliExpress FR : recherche, consultation d'articles et avis clients vérifiés.

Expose les outils MCP pour Claude Desktop, Cursor et agents ChatGPT :
- search_aliexpress_products : recherche par mots-clés, filtres de prix, tri et livraison gratuite
- get_aliexpress_product_details : détails d'un article, prix, photos HD et garanties
- get_aliexpress_product_reviews : avis clients authentiques, notes étoiles et photos réelles
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Annotated, Any, Literal

import anyio.to_thread
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from .scraper import AliExpressScraper

logger = logging.getLogger("aliexpress_mcp")
logger.setLevel(logging.INFO)

INSTRUCTIONS = """\
Serveur MCP officiel pour AliExpress France (prix en euros, livraison en France métropolitaine).

Outils disponibles :
- search_aliexpress_products : Recherche d'articles avec filtres (prix, tri, livraison gratuite).
- get_aliexpress_product_details : Fiche détaillée d'un article avec galerie de photos et prix.
- get_aliexpress_product_reviews : Avis et évaluations réels d'acheteurs avec notes, pays et photos.
"""

mcp = MCPServer(name="AliExpress FR", instructions=INSTRUCTIONS)
scraper = AliExpressScraper()

# Verrou pour sérialiser les requêtes (queue FIFO) et temporisation humaine
REQUEST_QUEUE_LOCK = asyncio.Lock()
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)


async def _human_paced_call(func, *args, **kwargs):
    """Exécute un appel bloquant de manière sérialisée avec un léger délai aléatoire."""
    async with REQUEST_QUEUE_LOCK:
        # Pause humaine aléatoire entre 0.4s et 1.0s
        jitter = random.uniform(0.4, 1.0)
        await asyncio.sleep(jitter)
        try:
            return await anyio.to_thread.run_sync(lambda: func(*args, **kwargs))
        except Exception as exc:
            logger.error(f"Erreur d'exécution: {exc}")
            raise ToolError(f"Erreur AliExpress: {exc}") from None


@mcp.tool(
    name="search_aliexpress_products",
    title="Rechercher des produits sur AliExpress FR",
    annotations=READ_ONLY,
)
async def search_aliexpress_products(
    ctx: Context,
    query: Annotated[
        str,
        Field(description="Mots-clés de recherche en français (ex: 'esp32', 'chargeur gan 65w', 'tournevis precision')."),
    ],
    page: Annotated[
        int,
        Field(ge=1, le=50, description="Numéro de page de résultats (défaut: 1)."),
    ] = 1,
    sort: Annotated[
        Literal["default", "price_asc", "price_desc", "orders"],
        Field(description="Critère de tri : 'default', 'price_asc' (prix croissant), 'price_desc' (prix décroissant), 'orders' (meilleures ventes)."),
    ] = "default",
    min_price: Annotated[
        float | None,
        Field(ge=0, description="Prix minimum en euros."),
    ] = None,
    max_price: Annotated[
        float | None,
        Field(ge=0, description="Prix maximum en euros."),
    ] = None,
    free_shipping: Annotated[
        bool,
        Field(description="Filtrer uniquement les articles avec livraison gratuite."),
    ] = False,
) -> dict[str, Any]:
    """Recherche des produits sur AliExpress France avec filtres de prix, tri et livraison gratuite."""
    res = await _human_paced_call(
        scraper.search_products,
        query=query,
        page=page,
        sort=sort,
        min_price=min_price,
        max_price=max_price,
        free_shipping=free_shipping,
    )
    return res.model_dump()


@mcp.tool(
    name="get_aliexpress_product_details",
    title="Obtenir les détails d'un produit AliExpress",
    annotations=READ_ONLY,
)
async def get_aliexpress_product_details(
    ctx: Context,
    product_id_or_url: Annotated[
        str,
        Field(description="Identifiant numérique (ex: '1005006860885924') ou URL complète de la fiche article AliExpress."),
    ],
) -> dict[str, Any]:
    """Récupère les informations détaillées d'un produit AliExpress : titre complet, prix, galerie photos et notation."""
    res = await _human_paced_call(scraper.get_product_details, product_id_or_url)
    return res.model_dump()


@mcp.tool(
    name="get_aliexpress_product_reviews",
    title="Obtenir les avis clients vérifiés et évaluations",
    annotations=READ_ONLY,
)
async def get_aliexpress_product_reviews(
    ctx: Context,
    product_id_or_url: Annotated[
        str,
        Field(description="Identifiant numérique ou URL de l'article AliExpress."),
    ],
    page: Annotated[
        int,
        Field(ge=1, le=50, description="Numéro de page d'avis (défaut: 1)."),
    ] = 1,
    page_size: Annotated[
        int,
        Field(ge=1, le=20, description="Nombre d'avis par page (max 20)."),
    ] = 10,
    filter_type: Annotated[
        Literal["all", "local", "image"],
        Field(description="Filtre des avis : 'all' (tous), 'local' (acheteurs français / locaux), 'image' (avis avec photos réelles)."),
    ] = "all",
) -> dict[str, Any]:
    """Récupère les avis authentiques des acheteurs, les notes étoiles et les photos partagées par les clients."""
    res = await _human_paced_call(
        scraper.get_product_reviews,
        product_id_or_url=product_id_or_url,
        page=page,
        page_size=page_size,
        filter_type=filter_type,
    )
    return res.model_dump()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Serveur MCP AliExpress FR")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Protocole de transport (stdio pour CLI/Claude Desktop, sse pour HTTP)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Adresse d'écoute pour le mode HTTP/SSE")
    parser.add_argument("--port", type=int, default=8001, help="Port d'écoute HTTP/SSE (défaut: 8001)")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
