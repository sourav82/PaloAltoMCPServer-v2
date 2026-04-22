
def parse_traffic_logs(raw_logs):
    entries = raw_logs.get("entry", [])

    if isinstance(entries, dict):
        entries = [entries]

    parsed = []

    for e in entries:
        parsed.append({
            "src_ip": e.get("src"),
            "dst_ip": e.get("dst"),
            "src_port": e.get("sport"),
            "dst_port": e.get("dport"),
            "action": e.get("action"),
            "rule": e.get("rule"),
            "app": e.get("app"),
            "bytes": e.get("bytes"),
            "start_time": e.get("start"),
            "end_time": e.get("end"),
            "protocol": e.get("proto"),
            "bytes_sent": e.get("bytes_sent"),
            "bytes_received": e.get("bytes_received"),
            "packets": e.get("packets"),
            "session_end_reason": e.get("session_end_reason")
        })

    return parsed


def parse_threat_logs(raw_logs):
    entries = raw_logs.get("entry", [])

    if isinstance(entries, dict):
        entries = [entries]

    parsed = []

    for e in entries:
        parsed.append({
            "src_ip": e.get("src"),
            "dst_ip": e.get("dst"),
            "src_port": e.get("sport"),
            "dst_port": e.get("dport"),
            "action": e.get("action"),
            "rule": e.get("rule"),
            "threat_id": e.get("threatid"),
            "threat_name": e.get("threat_name"),
            "severity": e.get("severity"),
            "direction": e.get("direction"),
            "app": e.get("app"),
            "start_time": e.get("start"),
            "end_time": e.get("end"),
            "bytes": e.get("bytes"),
            "packets": e.get("packets"),
            "src_user": e.get("srcuser"),
            "dst_user": e.get("dstuser"),
            "src_zone": e.get("from"),
            "dst_zone": e.get("to"),
            "device_name": e.get("device_name"),
            "file_digest": e.get("filedigest"),
            "file_type": e.get("filetype"),
            "url": e.get("url")
        })

    return parsed


def parse_url_logs(raw_logs):
    entries = raw_logs.get("entry", [])

    if isinstance(entries, dict):
        entries = [entries]

    parsed = []

    for e in entries:
        parsed.append({
            "src_ip": e.get("src"),
            "dst_ip": e.get("dst"),
            "src_port": e.get("sport"),
            "dst_port": e.get("dport"),
            "action": e.get("action"),
            "rule": e.get("rule"),
            "url": e.get("url"),
            "category": e.get("category"),
            "app": e.get("app"),
            "start_time": e.get("start"),
            "end_time": e.get("end"),
            "bytes": e.get("bytes"),
            "packets": e.get("packets"),
            "src_user": e.get("srcuser"),
            "dst_user": e.get("dstuser"),
            "src_zone": e.get("from"),
            "dst_zone": e.get("to"),
            "device_name": e.get("device_name"),
            "url_category": e.get("url_category"),
            "http_method": e.get("http_method"),
            "referer": e.get("referer"),
            "user_agent": e.get("user_agent")
        })

    return parsed
