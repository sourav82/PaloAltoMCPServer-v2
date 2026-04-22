# Palo Alto MCP Server - AI Agent Instructions

## Architecture Overview
This is a Model Context Protocol (MCP) server for Palo Alto Panorama log analysis. The server provides tools to query threat and traffic logs from Panorama appliances.

**Core Components:**
- `tools/threat.py` & `tools/traffic.py`: MCP tool implementations for log searches
- `app/panorama_client.py`: Handles Panorama API authentication and XML-based queries
- `app/keyvault_client.py`: Azure Key Vault integration for secure credential storage
- `services/session_store.py`: In-memory session caching (replace with Redis for production)
- `app/parser.py`: XML log parsing utilities

## Key Patterns & Conventions

### Configuration
- All configuration via environment variables (see `app/config.py`)
- Secrets stored in Azure Key Vault, accessed via `get_secret(name)` from `app/keyvault_client.py`
- Example: Panorama credentials retrieved as `get_secret("panorama-username")` and `get_secret("panorama-password")`

### Panorama API Integration
- XML-based REST API with job-based asynchronous queries
- Authentication: Generate API key using username/password, then use key for subsequent requests
- Query workflow: Submit job → Poll for completion → Retrieve results
- Log types: "threat" and "traffic" with different parsing logic

### MCP Tool Structure
```python
@mcp.tool()
def tool_name(context: MCPContext, param: type = None):
    # Query Panorama
    raw = client.query_logs(query, log_type)
    # Parse results
    parsed = parse_function(raw)
    # Update session cache
    update_session(context.session_id, {"key": result})
    return result
```

### Session Management
- Each tool call receives `MCPContext` with `session_id`
- Cache results in session store for potential cross-tool correlation
- Current implementation is in-memory dict (not persistent)

### Log Parsing
- Raw logs are XML dict structures from `xmltodict`
- Parser extracts specific fields into structured dicts
- Traffic logs include: src_ip, dst_ip, ports, action, rule, app, bytes, start_time

## Development Workflow

### Running the Server
```bash
# Set environment variables for Panorama URL, Key Vault, Azure credentials
python paloalto.py
```

### Adding New Tools
1. Create tool function in `tools/` with `@mcp.tool()` decorator
2. Accept `MCPContext` as first parameter
3. Use PanoramaClient for API calls
4. Parse results and update session
5. Return structured data

### Testing
- Tools are designed for integration testing with live Panorama
- Mock Panorama responses for unit testing
- Validate XML parsing and session updates

## Dependencies
- `mcp[cli]`: FastMCP server framework
- `azure-identity` & `azure-keyvault-secrets`: Azure authentication
- `xmltodict`: XML parsing
- `httpx` & `requests`: HTTP clients

## Security Notes
- Never log or expose API keys or credentials
- Use Key Vault for all sensitive configuration
- Validate SSL certificates in production