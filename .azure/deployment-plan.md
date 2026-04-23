# Deployment Plan

## Status
Ready for Validation

## Goal
Prepare the Palo Alto MCP server for deployment to Azure Container Apps as a long-running HTTP MCP service.

## App Summary
- Runtime: Python
- Current hosting model: Azure Functions adapter plus standalone MCP HTTP entrypoint
- Target hosting model: Azure Container Apps running the MCP `streamable_http_app()`
- Scope: prepare code and deployment assets; do not execute Azure deployment yet

## Architecture
- One Azure Container Registry to store the image
- One Azure Container Apps Environment to host the app
- One Azure Container App for the MCP server
- One Log Analytics workspace for environment logs
- Reuse existing Key Vault: `https://kv-secret-001.vault.azure.net`
- No VNet integration required for this PoC because the firewall is reachable over public IP

## Azure Resources
- Resource group
- Azure Container Registry
- Log Analytics workspace
- Azure Container Apps Environment
- Azure Container App
- Existing Key Vault only, no new Key Vault
- Prefer system-assigned managed identity only if needed for Key Vault access
- No VNet or private networking resources for the PoC

## Planned Code Changes
- Make the HTTP MCP entrypoint the primary container startup path
- Ensure all MCP tools, including policies, are imported in the HTTP server entrypoint
- Add a production-ready Dockerfile
- Add a `.dockerignore`
- Add Container Apps deployment guidance and required environment variables
- Keep Azure Functions files in place unless explicitly removed later

## Completed Changes
- Imported `policies` into the HTTP MCP entrypoint so the tool is available in Container Apps
- Added a root `Dockerfile` for Azure Container Apps deployment
- Added a root `.dockerignore`
- Lowered package metadata requirement to Python 3.11 for a practical container runtime target
- Added step-by-step Azure Container Apps provisioning and testing guidance to `paloalto/README.md`

## Client Impact
- Client continues calling MCP over HTTP/JSON-RPC
- Base URL changes from Azure Functions endpoint to the Container App FQDN
- No Azure Functions route conventions required
- Health endpoint remains available
- Sessions continue to work if the client stays on HTTP MCP and the app remains stateful

## Validation
- Local container build succeeds
- Python compile check succeeds
- HTTP health endpoint is reachable in container mode
- MCP server starts with `MCP_TRANSPORT=http`

## Cost Notes
- Optimize for PoC cost, not high availability
- Use a single Container App replica with low CPU and memory
- Use the smallest practical Azure Container Registry SKU
- Use one Container Apps Environment and one Log Analytics workspace only
- Avoid extra networking resources since public connectivity is acceptable
