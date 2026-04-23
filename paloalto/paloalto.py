
#!/usr/bin/env python3
"""
Unified MCP Server for Palo Alto Panorama logs
Supports both stdio (local) and HTTP (remote) transports
"""
import os
import sys
import logging
from starlette.responses import JSONResponse
from mcp.server.transport_security import TransportSecuritySettings
from tools import mcp, threat, traffic, url, policies

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_stdio():
    """Run the MCP server with stdio transport (for local development)"""
    logger.info("Starting MCP server with stdio transport")
    mcp.run(transport="stdio")

@mcp.custom_route("/health", methods=["GET"])
def health_check(request):
    return JSONResponse({"status": "healthy", "server": "Palo Alto MCP Server"})


def run_http():
    """Run the MCP server with HTTP transport (for remote deployment)"""
    import uvicorn

    logger.info("Starting MCP server with HTTP transport")

    # Use stateless HTTP so standard MCP JSON-RPC calls work without
    # session negotiation headers in simple clients and PoC testing.
    mcp.settings.stateless_http = True
    # Container Apps uses an external hostname, so disable the localhost-only
    # default host restriction for PoC HTTP deployments.
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    )

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))

    app = mcp.streamable_http_app()

    logger.info(f"Starting HTTP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

def main():
    """Main entry point - auto-detect transport based on environment/command line"""
    transport = os.getenv('MCP_TRANSPORT', 'stdio').lower()

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['http', 'stdio']:
            transport = sys.argv[1]

    logger.info(f"Starting Palo Alto MCP Server with {transport} transport")

    if transport == 'http':
        run_http()
    elif transport == 'stdio':
        run_stdio()
    else:
        logger.error(f"Unknown transport: {transport}. Use 'stdio' or 'http'")
        sys.exit(1)

if __name__ == "__main__":
    main()
