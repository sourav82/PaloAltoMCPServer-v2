"""
Azure Functions HTTP endpoint for Panorama MCP Server
"""
import logging
import json
import azure.functions as func
from tools import mcp, threat, traffic, url

# Set up logging for Azure Functions
logging.basicConfig(level=logging.INFO)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Functions HTTP trigger for MCP server"""

    try:
        # Get request body
        req_body = req.get_json()
        method = req_body.get('method', '')
        params = req_body.get('params', {})

        logging.info(f"MCP Request: {method}")

        # Route MCP requests
        if method == 'tools/list':
            # List available tools
            tools = []
            for tool_name in ['search_threat_logs', 'search_traffic_logs', 'search_url_logs']:
                tools.append({
                    'name': tool_name,
                    'description': f'Search {tool_name.split("_")[1]} logs',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'context': {'type': 'object'},
                            'src_ip': {'type': 'string'},
                            'dst_ip': {'type': 'string'}
                        }
                    }
                })

            response = {
                'jsonrpc': '2.0',
                'id': req_body.get('id'),
                'result': {'tools': tools}
            }

        elif method == 'tools/call':
            # Execute tool
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})

            # Create mock context for Azure Functions
            context = type('MockContext', (), {'session_id': 'azure-functions'})()

            result = None
            if tool_name == 'search_threat_logs':
                result = threat.search_threat_logs(context, **tool_args)
            elif tool_name == 'search_traffic_logs':
                result = traffic.search_traffic_logs(context, **tool_args)
            elif tool_name == 'search_url_logs':
                result = url.search_url_logs(context, **tool_args)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            response = {
                'jsonrpc': '2.0',
                'id': req_body.get('id'),
                'result': result
            }

        else:
            response = {
                'jsonrpc': '2.0',
                'id': req_body.get('id'),
                'error': {'code': -32601, 'message': f'Method not found: {method}'}
            }

        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        error_response = {
            'jsonrpc': '2.0',
            'id': req_body.get('id') if 'req_body' in locals() else None,
            'error': {'code': -32000, 'message': str(e)}
        }
        return func.HttpResponse(
            json.dumps(error_response),
            mimetype="application/json",
            status_code=500
        )