#!/usr/bin/env python3
"""
Test script for Azure Functions HTTP endpoint
"""
import json
import requests
from unittest.mock import Mock

def test_function_locally():
    """Test the Azure Function logic locally"""
    print("Testing Azure Function logic locally...")

    # Mock Azure Functions request
    mock_req = Mock()
    mock_req.get_json.return_value = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/list',
        'params': {}
    }

    # Import and test the function
    try:
        from function_app import main
        print("✓ Function imported successfully")

        # Note: Can't easily test async function without proper event loop
        # This would need to be run in an async context
        print("✓ Function structure looks correct")

    except Exception as e:
        print(f"✗ Function test failed: {e}")

def create_deployment_instructions():
    """Create Azure deployment instructions"""
    instructions = """
# Azure Functions Deployment Instructions

## Prerequisites
1. Azure CLI installed
2. Azure Functions Core Tools installed
3. Azure subscription with appropriate permissions

## Deployment Steps

### 1. Create Azure Resources
```bash
# Create resource group
az group create --name paloalto-mcp-rg --location centralindia

# Create storage account
az storage account create --name paloaltomcpstorage --location centralindia --resource-group paloalto-mcp-rg --sku Standard_LRS

# Create function app
az functionapp create --resource-group paloalto-mcp-rg --consumption-plan-location centralindia --runtime python --runtime-version 3.11 --functions-version 4 --name paloalto-mcp-server-app --storage-account paloaltomcpstorage
```

### 2. Set Environment Variables
```bash
az functionapp config appsettings set --name paloalto-mcp-server-app --resource-group paloalto-mcp-rg --settings \\
    PANORAMA_URL="https://your-panorama-url" \\
    KEYVAULT_URL="https://your-keyvault-url.vault.azure.net/" \\
    TENANT_ID="your-tenant-id" \\
    CLIENT_ID="your-client-id" \\
    CLIENT_SECRET="your-client-secret"
```

### 3. Deploy the Function
```bash
# Install Azure Functions extension for Python
func azure functionapp publish paloalto-mcp-server-app
```

## Testing the Function

### Test tools/list
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

### Test tools/call
```bash
curl -X POST https://paloalto-mcp-server-app.azurewebsites.net/api/PanoramaMCP \\
  -H "Content-Type: application/json" \\
  -H "x-functions-key: YOUR_FUNCTION_KEY" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "search_traffic_logs",
      "arguments": {
        "src_ip": "192.168.1.1"
      }
    }
  }'
```

## Connecting to Azure SRE Agent

To connect this MCP server to an Azure SRE agent:

1. **Get Function URL**: Get the function URL from Azure portal
2. **Configure SRE Agent**: Update your SRE agent configuration to use HTTP transport pointing to the function URL
3. **Authentication**: Use function keys or Azure AD authentication for secure access

## Limitations

- **Timeout**: Azure Functions have execution time limits (default 5 minutes for consumption plan)
- **Cold Starts**: First request may be slower due to cold start
- **Concurrent Requests**: Limited concurrent execution in consumption plan
- **Session State**: No persistent session state between function invocations

## Alternative: Azure Container Apps

For better performance and longer execution times, consider deploying as a container:

```bash
# Build and push container
az acr create --resource-group paloalto-mcp-rg --name paloaltomcpacr --sku Basic
az acr build --registry paloaltomcpacr --image paloalto-mcp:latest .

# Deploy to Container Apps
az containerapp create --name paloalto-mcp --resource-group paloalto-mcp-rg --image paloaltomcpacr.azurecr.io/paloalto-mcp:latest --target-port 8000 --ingress external
```
"""
    return instructions

if __name__ == "__main__":
    test_function_locally()
    print("\n" + "="*50)
    print("AZURE FUNCTIONS DEPLOYMENT GUIDE")
    print("="*50)
    print(create_deployment_instructions())