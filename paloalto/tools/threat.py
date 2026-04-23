from app.context import build_context
from app.panorama_client import PanoramaClient
from app.parser import parse_threat_logs
from services.session_store import update_session
from tools import mcp


client = PanoramaClient()

@mcp.tool()
def search_threat_logs(
    session_id: str = None,
    src_ip: str = None,
    dst_ip: str = None,
    threat_id: str = None,
    severity: str = None
):
    context = build_context(session_id)
    filters = []

    if src_ip:
        filters.append(f"(addr.src in {src_ip})")

    if dst_ip:
        filters.append(f"(addr.dst in {dst_ip})")

    if threat_id:
        filters.append(f"(threatid eq {threat_id})")

    if severity:
        filters.append(f"(severity eq '{severity}')")

    query = " and ".join(filters) if filters else ""

    raw = client.query_logs(query, "threat")
    parsed = parse_threat_logs(raw)

    # Determine overall threat assessment
    high_severity_count = sum(1 for log in parsed if log.get("severity") == "high")
    critical_severity_count = sum(1 for log in parsed if log.get("severity") == "critical")

    result = {
        "session_id": context.session_id,
        "threat_count": len(parsed),
        "high_severity_count": high_severity_count,
        "critical_severity_count": critical_severity_count,
        "logs": parsed[:100]  # Limit to first 100 logs for AI processing
    }

    update_session(context.session_id, {"threat": result})

    return result
