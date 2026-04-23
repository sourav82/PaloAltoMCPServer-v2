import ipaddress

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


def _normalize_entries(value):
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    return []


def _extract_member_values(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        members = []
        for item in value:
            members.extend(_extract_member_values(item))
        return members
    if isinstance(value, dict):
        if "member" in value:
            return _extract_member_values(value.get("member"))

        member_value = value.get("#text") or value.get("@name") or value.get("name")
        if member_value:
            return [member_value]

    return []


def _collect_policy_object_names(policy: dict):
    names = set()
    for field in ["source", "destination", "service", "application"]:
        value = policy.get(field)
        if value is None:
            continue
        names.update(_extract_member_values(value))
    return names


def _get_device_entries():
    data = client.get_config("/config/devices/entry")
    return _normalize_entries(data.get("entry", []))


def _get_config_entries(xpaths: list[str]):
    entries = []
    seen_names = set()

    for xpath in xpaths:
        data = client.get_config(xpath)
        for entry in _normalize_entries(data.get("entry", [])):
            if not isinstance(entry, dict):
                continue

            name = entry.get("@name")
            dedupe_key = (xpath, name)
            if dedupe_key in seen_names:
                continue

            seen_names.add(dedupe_key)
            entries.append(entry)

    return entries


def _load_objects(vsys: str, object_type: str):
    device_entries = _get_device_entries()

    if object_type == "address":
        object_suffix = "address/entry"
        shared_path = "/config/shared/address/entry"
    elif object_type == "service":
        object_suffix = "service/entry"
        shared_path = "/config/shared/service/entry"
    elif object_type == "address-group":
        object_suffix = "address-group/entry"
        shared_path = "/config/shared/address-group/entry"
    elif object_type == "service-group":
        object_suffix = "service-group/entry"
        shared_path = "/config/shared/service-group/entry"
    else:
        return {}

    xpaths = [
        f"/config/devices/entry/vsys/entry[@name='{vsys}']/{object_suffix}",
    ]

    for device_entry in device_entries:
        device_name = device_entry.get("@name")
        if not device_name:
            continue

        xpaths.extend([
            f"/config/devices/entry[@name='{device_name}']/vsys/entry[@name='{vsys}']/{object_suffix}",
        ])

    xpaths.append(shared_path)
    entries = _get_config_entries(xpaths)

    return {entry.get("@name"): entry for entry in entries if entry.get("@name")}


def _extract_group_member_names(group_entry: dict):
    member_names = set()

    def add_members(member_value):
        if member_value is None:
            return
        if isinstance(member_value, dict):
            # xmltodict may produce a dict for a single member
            member_value = [member_value]
        if isinstance(member_value, str):
            member_names.add(member_value)
            return
        for item in member_value:
            if isinstance(item, dict):
                name = item.get("#text") or item.get("@name") or item.get("name")
                if name:
                    member_names.add(name)
            elif isinstance(item, str):
                member_names.add(item)

    if "static" in group_entry and isinstance(group_entry["static"], dict):
        add_members(group_entry["static"].get("member"))
    if "members" in group_entry:
        add_members(group_entry["members"].get("member") if isinstance(group_entry["members"], dict) else group_entry["members"])
    if "member" in group_entry:
        add_members(group_entry["member"])

    return member_names


def _resolve_address_group_members(group_name: str, address_group_map: dict, address_map: dict, visited=None):
    if visited is None:
        visited = set()
    if group_name in visited:
        return []
    visited.add(group_name)

    group_entry = address_group_map.get(group_name)
    if not group_entry:
        return []

    member_names = _extract_group_member_names(group_entry)
    resolved = {}
    for member_name in member_names:
        if member_name in address_map:
            resolved[member_name] = address_map[member_name]
        elif member_name in address_group_map:
            for entry in _resolve_address_group_members(member_name, address_group_map, address_map, visited):
                if entry.get("@name"):
                    resolved[entry.get("@name")] = entry

    return list(resolved.values())


def _resolve_service_group_members(group_name: str, service_group_map: dict, service_map: dict, visited=None):
    if visited is None:
        visited = set()
    if group_name in visited:
        return []
    visited.add(group_name)

    group_entry = service_group_map.get(group_name)
    if not group_entry:
        return []

    member_names = _extract_group_member_names(group_entry)
    resolved = {}
    for member_name in member_names:
        if member_name in service_map:
            resolved[member_name] = service_map[member_name]
        elif member_name in service_group_map:
            for entry in _resolve_service_group_members(member_name, service_group_map, service_map, visited):
                if entry.get("@name"):
                    resolved[entry.get("@name")] = entry

    return list(resolved.values())


def _address_entry_contains_ip(address_entry: dict, ip_address: str):
    if not address_entry or not ip_address:
        return False

    def parse_user_network(ip_str: str):
        try:
            if "/" in ip_str:
                return ipaddress.ip_network(ip_str, strict=False)
            return ipaddress.ip_network(ipaddress.ip_address(ip_str))
        except ValueError:
            return None

    user_network = parse_user_network(ip_address)
    if not user_network:
        return False

    def check_network_overlap(policy_value: str):
        try:
            if "/" in policy_value:
                policy_network = ipaddress.ip_network(policy_value, strict=False)
            else:
                policy_network = ipaddress.ip_network(ipaddress.ip_address(policy_value))
            
            return (
                user_network.subnet_of(policy_network) or
                policy_network.subnet_of(user_network) or
                user_network.overlaps(policy_network)
            )
        except ValueError:
            return False

    if "ip-netmask" in address_entry:
        if check_network_overlap(address_entry["ip-netmask"]):
            return True
    
    if "ip-range" in address_entry:
        range_value = address_entry["ip-range"]
        if isinstance(range_value, str) and "-" in range_value:
            start, end = range_value.split("-", 1)
            try:
                start_ip = ipaddress.ip_address(start.strip())
                end_ip = ipaddress.ip_address(end.strip())
                start_net = ipaddress.ip_network(start_ip)
                end_net = ipaddress.ip_network(end_ip)
                if check_network_overlap(str(start_net)) or check_network_overlap(str(end_net)):
                    return True
            except ValueError:
                pass
    
    return False


def _service_entry_contains_port(service_entry: dict, port: str):
    if not service_entry or not port:
        return False

    def port_in_range(port_str: str, target_port: str):
        try:
            target = int(target_port)
            if "-" in port_str:
                start, end = port_str.split("-", 1)
                return int(start) <= target <= int(end)
            return int(port_str) == target
        except ValueError:
            return False

    if "protocol" in service_entry:
        proto = service_entry.get("protocol", {})
        if isinstance(proto, dict):
            for proto_name, proto_data in proto.items():
                if isinstance(proto_data, dict):
                    for port_field in ["port", "destination-port", "source-port"]:
                        if port_field in proto_data:
                            port_value = proto_data[port_field]
                            if isinstance(port_value, str) and port_in_range(port_value, port):
                                return True

    return False


def _policy_matches_ip(policy: dict, ip_address: str, address_map: dict, address_group_map: dict, field_name: str):
    if not ip_address:
        return True

    value = policy.get(field_name)
    names = set(_extract_member_values(value))

    if value is None or "any" in names:
        return True

    for name in names:
        if name == "any":
            return True
        if name in address_map and _address_entry_contains_ip(address_map[name], ip_address):
            return True
        if name in address_group_map:
            for entry in _resolve_address_group_members(name, address_group_map, address_map):
                if _address_entry_contains_ip(entry, ip_address):
                    return True
    return False


def _policy_matches_service(policy: dict, port: str, service_map: dict, service_group_map: dict):
    if not port:
        return True

    value = policy.get("service")
    names = set(_extract_member_values(value))

    if value is None or "any" in names:
        return True

    for name in names:
        if name == "any":
            return True
        if name in service_map and _service_entry_contains_port(service_map[name], port):
            return True
        if name in service_group_map:
            for entry in _resolve_service_group_members(name, service_group_map, service_map):
                if _service_entry_contains_port(entry, port):
                    return True
    return False


def _get_virtual_routers(vsys: str):
    xpath = "/config/devices/entry/network/virtual-router/entry"
    data = client.get_config(xpath)
    return _normalize_entries(data.get("entry", []))


def _get_static_routes(vsys: str, virtual_router: str = None):
    router_entries = []

    if virtual_router:
        router_entries = [{"@name": virtual_router}]
    else:
        router_entries = _get_virtual_routers(vsys)

    routes = []
    for router in router_entries:
        router_name = router.get("@name")
        if not router_name:
            continue

        xpath = (
            "/config/devices/entry"
            f"/network/virtual-router/entry[@name='{router_name}']"
            "/routing-table/ip/static-route/entry"
        )
        data = client.get_config(xpath)
        for route in _normalize_entries(data.get("entry", [])):
            if isinstance(route, dict):
                route_with_router = dict(route)
                route_with_router["_virtual_router"] = router_name
                routes.append(route_with_router)

    return routes


def _build_interface_zone_map(zone_interface_map: dict):
    interface_zone_map = {}
    for zone_name, interfaces in zone_interface_map.items():
        for interface in interfaces:
            interface_zone_map[interface] = zone_name
    return interface_zone_map


def _get_route_interface(route: dict):
    if not isinstance(route, dict):
        return None

    interface = route.get("interface")
    if isinstance(interface, str):
        return interface

    if isinstance(interface, dict):
        return interface.get("#text") or interface.get("@name") or interface.get("member")

    nexthop = route.get("nexthop")
    if isinstance(nexthop, dict):
        nh_interface = nexthop.get("interface")
        if isinstance(nh_interface, str):
            return nh_interface
        if isinstance(nh_interface, dict):
            return nh_interface.get("#text") or nh_interface.get("@name") or nh_interface.get("member")

    return None


def _get_zone_for_ip(ip_address: str, static_routes: list[dict], interface_zone_map: dict):
    if not ip_address or not static_routes:
        return None

    try:
        user_network = ipaddress.ip_network(ip_address, strict=False)
    except ValueError:
        return None

    best_match = None
    best_prefix_len = -1

    for route in static_routes:
        if not isinstance(route, dict):
            continue

        destination = route.get("destination")
        route_interface = _get_route_interface(route)
        zone = interface_zone_map.get(route_interface)

        if not destination or not zone:
            continue

        try:
            route_network = ipaddress.ip_network(destination, strict=False)

            if user_network.subnet_of(route_network) or user_network == route_network:
                prefix_len = route_network.prefixlen
                if prefix_len > best_prefix_len:
                    best_match = zone
                    best_prefix_len = prefix_len
        except ValueError:
            continue

    return best_match


def _get_zone_from_interface_config(vsys: str):
    # Get zones and their interface members
    xpath = f"/config/devices/entry/vsys/entry[@name='{vsys}']/zone/entry"
    data = client.get_config(xpath)
    zones = _normalize_entries(data.get("entry", []))
    
    zone_interface_map = {}
    for zone in zones:
        zone_name = zone.get("@name")
        if not zone_name:
            continue
            
        # Get interface members of this zone
        interfaces = []
        if "network" in zone and isinstance(zone["network"], dict):
            network = zone["network"]
            if "layer3" in network:
                layer3 = network["layer3"]
                if isinstance(layer3, dict) and "member" in layer3:
                    member_data = layer3["member"]
                    if isinstance(member_data, list):
                        interfaces.extend(member_data)
                    elif isinstance(member_data, str):
                        interfaces.append(member_data)
        
        zone_interface_map[zone_name] = interfaces
    
    return zone_interface_map


def _get_interface_ip_networks(vsys: str):
    # Get interface configurations with IP addresses (interfaces are at device level, not vsys level)
    xpath = f"/config/devices/entry/network/interface/ethernet/entry"
    data = client.get_config(xpath)
    
    interface_networks = {}
    
    def extract_ip_from_layer3(layer3_config, interface_name):
        networks = []
        if isinstance(layer3_config, dict):
            if "ip" in layer3_config and isinstance(layer3_config["ip"], dict):
                ip_entries = _normalize_entries(layer3_config["ip"].get("entry", []))
                for ip_entry in ip_entries:
                    if isinstance(ip_entry, dict) and "@name" in ip_entry:
                        ip_addr = ip_entry["@name"]
                        try:
                            network = ipaddress.ip_network(ip_addr, strict=False)
                            networks.append(network)
                        except ValueError:
                            pass
        return networks
    
    interfaces = _normalize_entries(data.get("entry", []))
    for interface in interfaces:
        if not isinstance(interface, dict):
            continue
            
        interface_name = interface.get("@name")
        if not interface_name:
            continue
            
        networks = []
        
        # Check different interface types
        for if_type in ["layer3", "layer2", "tap", "tunnel"]:
            if if_type in interface and isinstance(interface[if_type], dict):
                networks.extend(extract_ip_from_layer3(interface[if_type], interface_name))
        
        if networks:
            interface_networks[interface_name] = networks
    
    return interface_networks


def _get_zone_for_ip_from_interfaces(ip_address: str, zone_interface_map: dict, interface_networks: dict):
    if not ip_address:
        return None

    try:
        user_network = ipaddress.ip_network(ip_address, strict=False)
    except ValueError:
        return None

    # Check each zone's interfaces
    for zone_name, interfaces in zone_interface_map.items():
        for interface in interfaces:
            if interface in interface_networks:
                for network in interface_networks[interface]:
                    if user_network.subnet_of(network) or user_network == network:
                        return zone_name
    
    return None


def _derive_zone_for_ip(ip_address: str, vsys: str, zone_interface_map: dict, interface_networks: dict, virtual_router: str = None):
    if not ip_address:
        return None

    derived_zone = _get_zone_for_ip_from_interfaces(ip_address, zone_interface_map, interface_networks)
    if derived_zone:
        return derived_zone

    static_routes = _get_static_routes(vsys, virtual_router)
    interface_zone_map = _build_interface_zone_map(zone_interface_map)
    return _get_zone_for_ip(ip_address, static_routes, interface_zone_map)


def _policy_matches_zone(policy: dict, field_name: str, zone_name: str):
    if not zone_name:
        return True

    return zone_name in set(_extract_member_values(policy.get(field_name)))


def _resolve_referenced_objects(policy_entries: list[dict], vsys: str):
    object_names = set()
    for policy in policy_entries:
        object_names.update(_collect_policy_object_names(policy))

    referenced = {
        "address": [],
        "service": [],
        "address_group": [],
        "service_group": [],
        "address_group_expansions": {},
        "service_group_expansions": {}
    }

    if not object_names:
        return referenced

    try:
        address_map = _load_objects(vsys, "address")
        service_map = _load_objects(vsys, "service")
        address_group_map = _load_objects(vsys, "address-group")
        service_group_map = _load_objects(vsys, "service-group")
    except Exception:
        return referenced

    for name in sorted(object_names):
        if name in address_map:
            referenced["address"].append(address_map[name])
        if name in service_map:
            referenced["service"].append(service_map[name])
        if name in address_group_map:
            referenced["address_group"].append(address_group_map[name])
            referenced["address_group_expansions"][name] = _resolve_address_group_members(
                name, address_group_map, address_map
            )
        if name in service_group_map:
            referenced["service_group"].append(service_group_map[name])
            referenced["service_group_expansions"][name] = _resolve_service_group_members(
                name, service_group_map, service_map
            )

    return referenced


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
    dst_zone: str = None,
    src_ip: str = None,
    dst_ip: str = None,
    service_port: str = None,
    virtual_router: str = None
):
    xpath = f"/config/devices/entry/vsys/entry[@name='{vsys}']/rulebase/security/rules/entry"
    data = client.get_config(xpath)

    policies = data.get("entry", [])
    if isinstance(policies, dict):
        policies = [policies]

    if name:
        policies = [p for p in policies if p.get("@name") == name]

    derived_src_zone = None
    derived_dst_zone = None

    if src_ip or dst_ip:
        zone_interface_map = _get_zone_from_interface_config(vsys)
        interface_networks = _get_interface_ip_networks(vsys)

        if src_ip:
            derived_src_zone = _derive_zone_for_ip(
                src_ip, vsys, zone_interface_map, interface_networks, virtual_router
            )
        if dst_ip:
            derived_dst_zone = _derive_zone_for_ip(
                dst_ip, vsys, zone_interface_map, interface_networks, virtual_router
            )

    final_src_zone = src_zone or derived_src_zone
    final_dst_zone = dst_zone or derived_dst_zone

    if final_src_zone:
        policies = [p for p in policies if _policy_matches_zone(p, "from", final_src_zone)]
    if final_dst_zone:
        policies = [p for p in policies if _policy_matches_zone(p, "to", final_dst_zone)]

    if src_ip or dst_ip or service_port:
        address_map = _load_objects(vsys, "address")
        address_group_map = _load_objects(vsys, "address-group")
        service_map = _load_objects(vsys, "service")
        service_group_map = _load_objects(vsys, "service-group")

        if address_map or address_group_map or service_map or service_group_map:
            policies = [
                p for p in policies
                if _policy_matches_ip(p, src_ip, address_map, address_group_map, "source")
                and _policy_matches_ip(p, dst_ip, address_map, address_group_map, "destination")
                and _policy_matches_service(p, service_port, service_map, service_group_map)
            ]

    referenced_objects = _resolve_referenced_objects(policies, vsys)

    result = {
        "entry": policies,
        "referenced_objects": referenced_objects,
        "zone_inference": {
            "src_ip": src_ip,
            "derived_src_zone": derived_src_zone,
            "final_src_zone": final_src_zone,
            "dst_ip": dst_ip,
            "derived_dst_zone": derived_dst_zone,
            "final_dst_zone": final_dst_zone
        }
    }

    return _save_session_result(context, "security_policies", result)


@mcp.tool()
def get_virtual_network_routes(
    context: MCPContext,
    vsys: str = "vsys1",
    virtual_router: str = None,
    name: str = None
):
    routes = _get_static_routes(vsys, virtual_router)

    if name:
        routes = [r for r in routes if r.get("@name") == name]

    return _save_session_result(context, "virtual_network_routes", {"entry": routes})
