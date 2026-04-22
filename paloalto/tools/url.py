from app.context import MCPContext
from services.session_store import update_session
from app.panorama_client import PanoramaClient
from app.parser import parse_url_logs
from services.session_store import update_session
from tools import mcp


client = PanoramaClient()

@mcp.tool()
def search_url_logs(
    context: MCPContext,
    src_ip: str = None,
    dst_ip: str = None,
    url: str = None,
    category: str = None,
    action: str = None
):
    filters = []

    if src_ip:
        filters.append(f"(addr.src in {src_ip})")

    if dst_ip:
        filters.append(f"(addr.dst in {dst_ip})")

    if url:
        filters.append(f"(url contains '{url}')")

    if category:
        filters.append(f"(category eq '{category}')")

    if action:
        filters.append(f"(action eq '{action}')")

    query = " and ".join(filters) if filters else ""

    raw = client.query_logs(query, "url")
    parsed = parse_url_logs(raw)

    # Categorize URL access patterns
    blocked_count = sum(1 for log in parsed if log.get("action") == "block")
    allowed_count = sum(1 for log in parsed if log.get("action") == "allow")

    # Group by categories
    category_counts = {}
    for log in parsed:
        cat = log.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    result = {
        "session_id": context.session_id,
        "url_count": len(parsed),
        "blocked_count": blocked_count,
        "allowed_count": allowed_count,
        "category_breakdown": category_counts,
        "logs": parsed[:100]  # Limit to first 100 logs for AI processing
    }

    update_session(context.session_id, {"url": result})

    return result