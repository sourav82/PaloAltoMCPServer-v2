"""
Azure Functions HTTP endpoint for Panorama MCP Server
"""
import logging
import json
import uuid
import azure.functions as func
from app.context import MCPContext
from tools import threat, traffic, url, policies

# Set up logging for Azure Functions
logging.basicConfig(level=logging.INFO)


def _build_session_context(req: func.HttpRequest) -> MCPContext:
    session_id = (
        req.headers.get('x-session-id')
        or req.params.get('session_id')
        or str(uuid.uuid4())
    )
    metadata = {
        'client_ip': req.headers.get('X-Forwarded-For') or req.headers.get('X-ARR-ClientIP'),
        'user_agent': req.headers.get('User-Agent'),
        'request_id': req.headers.get('x-ms-client-request-id')
    }
    return MCPContext(session_id=session_id, metadata=metadata)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Functions HTTP trigger for MCP server"""

    try:
        context = _build_session_context(req)

        # Get request body
        req_body = req.get_json()
        method = req_body.get('method', '')
        params = req_body.get('params', {})

        logging.info(f"MCP Request: {method}")

        # Route MCP requests
        if method == 'tools/list':
            # List available tools
            tools = []
            tool_definitions = [
                {
                    'name': 'search_threat_logs',
                    'description': 'Search threat logs',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'context': {'type': 'object'},
                            'src_ip': {'type': 'string'},
                            'dst_ip': {'type': 'string'},
                            'threat_id': {'type': 'string'},
                            'severity': {'type': 'string'}
                        }
                    }
                },
                {
                    'name': 'search_traffic_logs',
                    'description': 'Search traffic logs',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'context': {'type': 'object'},
                            'src_ip': {'type': 'string'},
                            'dst_ip': {'type': 'string'}
                        }
                    }
                },
                {
                    'name': 'search_url_logs',
                    'description': 'Search url logs',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'context': {'type': 'object'},
                            'src_ip': {'type': 'string'},
                            'dst_ip': {'type': 'string'},
                            'url': {'type': 'string'},
                            'category': {'type': 'string'},
                            'action': {'type': 'string'}
                        }
                    }
                },
                {
                    'name': 'get_nat_policies',
                    'description': 'Retrieve NAT policies',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'context': {'type': 'object'},
                            'vsys': {'type': 'string'},
                            'name': {'type': 'string'}
                        }
                    }
                },
                {
                    'name': 'get_security_policies',
                    'description': 'Retrieve security policies with optional IP, service/port, and zone filtering',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'context': {'type': 'object'},
                            'vsys': {'type': 'string'},
                            'name': {'type': 'string'},
                            'src_zone': {'type': 'string'},
                            'dst_zone': {'type': 'string'},
                            'src_ip': {'type': 'string'},
                            'dst_ip': {'type': 'string'},
                            'service_port': {'type': 'string'},
                            'virtual_router': {'type': 'string'}
                        }
                    }
                },
                {
                    'name': 'get_virtual_network_routes',
                    'description': 'Retrieve virtual network static routes',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'context': {'type': 'object'},
                            'vsys': {'type': 'string'},
                            'virtual_router': {'type': 'string'},
                            'name': {'type': 'string'}
                        }
                    }
                }
            ]
            for tool in tool_definitions:
                tools.append(tool)

            response = {
                'jsonrpc': '2.0',
                'id': req_body.get('id'),
                'result': {'tools': tools}
            }

        elif method == 'tools/call':
            # Execute tool
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})
            tool_args.pop('context', None)

            result = None
            if tool_name == 'search_threat_logs':
                result = threat.search_threat_logs(context, **tool_args)
            elif tool_name == 'search_traffic_logs':
                result = traffic.search_traffic_logs(context, **tool_args)
            elif tool_name == 'search_url_logs':
                result = url.search_url_logs(context, **tool_args)
            elif tool_name == 'get_nat_policies':
                result = policies.get_nat_policies(context, **tool_args)
            elif tool_name == 'get_security_policies':
                result = policies.get_security_policies(context, **tool_args)
            elif tool_name == 'get_virtual_network_routes':
                result = policies.get_virtual_network_routes(context, **tool_args)
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
