from app.context import MCPContext
from services.session_store import update_session
from app.panorama_client import PanoramaClient
from app.parser import parse_traffic_logs
from services.session_store import update_session
from tools import mcp


client = PanoramaClient()

@mcp.tool()
def search_traffic_logs(
    context: MCPContext,
    src_ip: str = None,
    dst_ip: str = None,
    port: int = None,
    action: str = None
):
    filters = []

    if src_ip:
        filters.append(f"(addr.src in {src_ip})")

    if dst_ip:
        filters.append(f"(addr.dst in {dst_ip})")

    if port:
        filters.append(f"(port.dst eq {port})")

    if action:
        filters.append(f"(action eq {action})")

    query = " and ".join(filters)

    raw = client.query_logs(query, "traffic")
    parsed = parse_traffic_logs(raw)

    # Analyze traffic patterns
    allow_count = sum(1 for log in parsed if log.get("action") == "allow")
    deny_count = sum(1 for log in parsed if log.get("action") == "deny")
    drop_count = sum(1 for log in parsed if log.get("action") == "drop")

    # Determine overall decision based on majority action
    decision = "unknown"
    if deny_count > allow_count and deny_count > drop_count:
        decision = "deny"
    elif allow_count > deny_count and allow_count > drop_count:
        decision = "allow"
    elif drop_count > allow_count and drop_count > deny_count:
        decision = "drop"

    # Calculate total bytes
    total_bytes = sum(int(log.get("bytes", 0)) for log in parsed if log.get("bytes"))

    result = {
        "session_id": context.session_id,
        "count": len(parsed),
        "allow_count": allow_count,
        "deny_count": deny_count,
        "drop_count": drop_count,
        "decision": decision,
        "total_bytes": total_bytes,
        "logs": parsed[:100]  # Limit to first 100 logs for AI processing
    }

    update_session(context.session_id, {"traffic": result})

    return result