from app.context import MCPContext
from services.session_store import update_session
from app.panorama_client import PanoramaClient
from tools import mcp

client = PanoramaClient()


def _save_session_result(context: MCPContext, key: str, data: dict):
    update_session(context.session_id, {key: data})
    return {
        "session_id": context.session_id,
        key: data
    }


@mcp.tool()
def get_nat_policies(
    context: MCPContext,
    vsys: str = "vsys1",
    name: str = None
):
    xpath = f"/config/devices/entry/vsys/entry[@name='{vsys}']/rulebase/nat/rules"
    data = client.get_config(xpath)

    if name:
        policies = data.get("entry", [])
        if isinstance(policies, dict):
            policies = [policies]
        policies = [p for p in policies if p.get("@name") == name]
        data = {"entry": policies}

    return _save_session_result(context, "nat_policies", data)


@mcp.tool()
def get_security_policies(
    context: MCPContext,
    vsys: str = "vsys1",
    name: str = None,
    src_zone: str = None,
    dst_zone: str = None
):
    xpath = f"/config/devices/entry/vsys/entry[@name='{vsys}']/rulebase/security/rules"
    data = client.get_config(xpath)

    policies = data.get("entry", [])
    if isinstance(policies, dict):
        policies = [policies]

    if name:
        policies = [p for p in policies if p.get("@name") == name]
    if src_zone:
        policies = [p for p in policies if p.get("from") == src_zone]
    if dst_zone:
        policies = [p for p in policies if p.get("to") == dst_zone]

    return _save_session_result(context, "security_policies", {"entry": policies})


@mcp.tool()
def get_virtual_network_routes(
    context: MCPContext,
    vsys: str = "vsys1",
    virtual_router: str = "default",
    name: str = None
):
    xpath = (
        f"/config/devices/entry/vsys/entry[@name='{vsys}']"
        f"/network/virtual-router/entry[@name='{virtual_router}']"
        "/routing-table/ip/static/entry"
    )
    data = client.get_config(xpath)

    routes = data.get("entry", [])
    if isinstance(routes, dict):
        routes = [routes]

    if name:
        routes = [r for r in routes if r.get("@name") == name]

    return _save_session_result(context, "virtual_network_routes", {"entry": routes})
