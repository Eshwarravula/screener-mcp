from mcp.server.transport_security import TransportSecuritySettings
from screener_mcp.server import mcp

# Configure FastMCP for Vercel's stateless serverless runtime.
mcp.settings.streamable_http_path = "/mcp"
mcp.settings.stateless_http = True
mcp.settings.json_response = True
mcp.settings.transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
)

app = mcp.streamable_http_app()
