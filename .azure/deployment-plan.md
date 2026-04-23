# Deployment Plan

## Status
Awaiting Approval

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
- Optional Key Vault for firewall credentials and other secrets
- Optional VNet integration if the firewall is reachable only through private networking

## Azure Resources
- Resource group
- Azure Container Registry
- Log Analytics workspace
- Azure Container Apps Environment
- Azure Container App
- Optional Key Vault
- Optional user-assigned or system-assigned managed identity
- Optional virtual network and subnet for private connectivity

## Planned Code Changes
- Make the HTTP MCP entrypoint the primary container startup path
- Ensure all MCP tools, including policies, are imported in the HTTP server entrypoint
- Add a production-ready Dockerfile
- Add a `.dockerignore`
- Add Container Apps deployment guidance and required environment variables
- Keep Azure Functions files in place unless explicitly removed later

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
