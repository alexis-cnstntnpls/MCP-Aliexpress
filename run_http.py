#!/usr/bin/env python3
"""Point d'entrée Streamable HTTP pour le serveur MCP AliExpress FR."""

import logging
import os
import sys
from pathlib import Path

# Ajouter src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from aliexpress_mcp.server import mcp
from mcp.server.transport_security import TransportSecuritySettings

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aliexpress-mcp")


def main():
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8001"))
    path = os.environ.get("MCP_PATH", "/mcp/aliexpress")

    public_host = os.environ.get("MCP_PUBLIC_HOST", "localhost")
    allowed_hosts = [
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",
        public_host,
        f"{public_host}:*",
        "*",
    ]

    security_settings = TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
        allowed_hosts=allowed_hosts,
        allowed_origins=["https://chatgpt.com", "https://claude.ai", "*"],
    )

    logger.info("Démarrage du serveur MCP AliExpress sur http://%s:%d%s", host, port, path)
    logger.info("Host public autorisé : %s", public_host)

    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        streamable_http_path=path,
        transport_security=security_settings,
    )


if __name__ == "__main__":
    main()
