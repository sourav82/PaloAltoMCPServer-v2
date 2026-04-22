# Palo Alto Panorama MCP Server

A Model Context Protocol (MCP) server for querying Palo Alto Panorama firewall logs, providing AI agents with access to threat, traffic, and URL filtering logs.

## Features

- **Threat Log Analysis**: Query threat logs with filtering by source/destination IP, threat ID, and severity
- **Traffic Log Analysis**: Search traffic logs with filtering by IPs, ports, actions, and rules
- **URL Filtering Logs**: Analyze URL access patterns and filtering decisions
- **Azure Integration**: Secure credential management via Azure Key Vault
- **JSON Output**: Structured log data optimized for AI agent consumption

## Local Development

### Prerequisites

- Python 3.11+
- Azure subscription with Key Vault access
- Palo Alto Panorama access

### Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Configure environment variables** (create `.env` file):
   ```env
   PANORAMA_URL=https://your-panorama-url
   KEYVAULT_URL=https://your-keyvault.vault.azure.net/
   TENANT_ID=your-tenant-id
   CLIENT_ID=your-client-id
   CLIENT_SECRET=your-client-secret
   ```

3. **Store Panorama credentials in Key Vault:**
   - `panorama-username`: Your Panorama username
   - `panorama-password`: Your Panorama password

4. **Run the server:**
   ```bash
   # Local development (stdio transport)
   python paloalto.py

   # Or explicitly specify transport
   python paloalto.py stdio

   # HTTP server for remote access
   python paloalto.py http

   # Or use environment variable
   MCP_TRANSPORT=http python paloalto.py
   ```

## HTTP Server Mode

When running in HTTP mode, the server provides REST endpoints:

- **POST `/mcp`** - MCP JSON-RPC endpoint
- **GET `/health`** - Health check endpoint

### HTTP Server Configuration

```bash
# Set custom host/port
HOST=0.0.0.0 PORT=8080 python paloalto.py http

# Default: localhost:8000
```

### Testing HTTP Endpoints

**Health check:**
```bash
curl http://localhost:8000/health
```

**List tools:**
```bash
curl -X POST http://localhost:8000/mcp \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

**Call tool:**
```bash
curl -X POST http://localhost:8000/mcp \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "search_traffic_logs",
      "arguments": {"src_ip": "192.168.1.1"}
    }
  }'
```

5. **Debug the server:**
   ```bash
   python debug.py
   ```

6. **Test transport modes:**
   ```bash
   python test_transports.py
   ```

## Azure Functions Deployment

### Quick Deploy

1. **Install Azure Functions Core Tools:**
   ```bash
   npm install -g azure-functions-core-tools@4
   ```

2. **Deploy to Azure:**
   ```bash
   # Set your Azure subscription
   az login
   az account set --subscription "your-subscription-id"

   # Run deployment script
   python azure_deploy.py
   ```

### Manual Deployment

1. **Create Azure resources:**
   ```bash
   # Create resource group
   az group create --name paloalto-mcp-rg --location centralindia

   # Create storage account
   az storage account create --name paloaltomcpstorage --location centralindia --resource-group paloalto-mcp-rg --sku Standard_LRS

   # Create function app
   az functionapp create --resource-group paloalto-mcp-rg --consumption-plan-location centralindia --runtime python --runtime-version 3.11 --functions-version 4 --name paloalto-mcp-server-app --storage-account paloaltomcpstorage
   ```

2. **Configure environment variables:**
   ```bash
   az functionapp config appsettings set --name paloalto-mcp-server-app --resource-group paloalto-mcp-rg --settings \\
       PANORAMA_URL="https://your-panorama-url" \\
       KEYVAULT_URL="https://your-keyvault-url.vault.azure.net/" \\
       TENANT_ID="your-tenant-id" \\
       CLIENT_ID="your-client-id" \\
       CLIENT_SECRET="your-client-secret"
   ```

3. **Deploy the function:**
   ```bash
   func azure functionapp publish paloalto-mcp-server-app
   ```

### Testing Azure Function

**List available tools:**
```bash
curl -X POST https://paloalto-mcp-server-app.azurewebsites.net/api/PanoramaMCP \\
  -H "Content-Type: application/json" \\
  -H "x-functions-key: YOUR_FUNCTION_KEY" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

**Query threat logs:**
```bash
curl -X POST https://paloalto-mcp-server-app.azurewebsites.net/api/PanoramaMCP \\
  -H "Content-Type: application/json" \\
  -H "x-functions-key: YOUR_FUNCTION_KEY" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "search_threat_logs",
      "arguments": {
        "src_ip": "192.168.1.100",
        "severity": "high"
      }
    }
  }'
```

## Connecting to Azure SRE Agent

1. **Get Function URL** from Azure Portal
2. **Configure your SRE agent** to use HTTP transport:
   ```json
   {
     "mcp_servers": {
       "panorama": {
         "transport": "http",
         "url": "https://paloalto-mcp-server-app.azurewebsites.net/api/PanoramaMCP",
         "headers": {
           "x-functions-key": "your-function-key"
         }
       }
     }
   }
   ```
3. **Use Azure AD authentication** for enhanced security instead of function keys

## Architecture

The server supports **dual transport modes** for maximum flexibility:

- **stdio Transport**: For local development and direct AI agent integration
- **HTTP Transport**: For remote deployment and web service integration

```
paloalto/
├── app/
│   ├── panorama_client.py    # Panorama API client
│   ├── keyvault_client.py    # Azure Key Vault integration
│   ├── parser.py            # Log parsing utilities
│   ├── context.py           # MCP context
│   └── config.py            # Configuration management
├── tools/
│   ├── threat.py            # Threat log queries
│   ├── traffic.py           # Traffic log queries
│   ├── url.py              # URL filtering queries
│   └── __init__.py         # MCP server setup
├── services/
│   └── session_store.py     # Session management
├── paloalto.py             # Unified server (stdio + HTTP)
├── function_app.py         # Azure Functions wrapper
├── debug.py                # Debugging utilities
└── azure_deploy.py         # Deployment helpers
```

## Security Considerations

- **SSL Verification**: Disabled for testing only (`verify=False` in requests)
- **Key Vault**: All sensitive credentials stored securely
- **Azure AD**: Use managed identities for production deployments
- **Network Security**: Restrict function access to authorized networks only

## Limitations

- **Azure Functions**: 5-minute timeout limit for consumption plan
- **Session State**: No persistent state between function invocations
- **Concurrent Requests**: Limited by consumption plan scaling

## Alternative Deployment: HTTP Server

For containerized or direct HTTP deployment:

```bash
# Run as HTTP server
python paloalto.py http

# Or with custom configuration
HOST=0.0.0.0 PORT=8080 python paloalto.py http
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["python", "paloalto.py", "http"]
```

```bash
# Build and run
docker build -t paloalto-mcp .
docker run -p 8000:8000 -e PANORAMA_URL="..." paloalto-mcp
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License
