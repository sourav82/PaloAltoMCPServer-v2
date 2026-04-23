#!/usr/bin/env python3
"""
MCP Tool Simulation Script
Simulates the get_security_policies tool call with mock Panorama data
"""
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_get_security_policies(vsys="vsys1", src_ip=None, service_port=None):
    """Simulate the get_security_policies tool with mock data"""

    # Mock Panorama API responses
    mock_policies_data = {
        "entry": [
            {
                "@name": "Policy-src-untrust-dst-internet",
                "from": "trust",
                "to": "untrust",
                "source": "any",
                "destination": "any",
                "service": "any",
                "action": "allow"
            },
            {
                "@name": "Policy-deny-all",
                "from": "any",
                "to": "any",
                "source": "any",
                "destination": "any",
                "service": "any",
                "action": "deny"
            }
        ]
    }

    mock_addresses_data = {
        "entry": [
            {"@name": "internal-net", "ip-netmask": "10.137.0.0/24"},
            {"@name": "dmz-net", "ip-netmask": "192.168.1.0/24"}
        ]
    }

    mock_services_data = {
        "entry": [
            {"@name": "http", "protocol": {"tcp": {"port": "80"}}},
            {"@name": "https", "protocol": {"tcp": {"port": "443"}}}
        ]
    }

    mock_zones_data = {
        "entry": [
            {
                "@name": "trust",
                "network": {
                    "layer3": {
                        "member": ["ethernet1/1", "ethernet1/2"]
                    }
                }
            },
            {
                "@name": "untrust",
                "network": {
                    "layer3": {
                        "member": ["ethernet1/3"]
                    }
                }
            }
        ]
    }

    mock_interfaces_data = {
        "entry": [
            {
                "@name": "ethernet1/1",
                "layer3": {
                    "ip": {
                        "entry": [
                            {
                                "@name": "10.137.0.1/24",
                                "member": "10.137.0.1/24"
                            }
                        ]
                    }
                }
            },
            {
                "@name": "ethernet1/3",
                "layer3": {
                    "ip": {
                        "entry": [
                            {
                                "@name": "203.0.113.1/24",
                                "member": "203.0.113.1/24"
                            }
                        ]
                    }
                }
            }
        ]
    }

    print("Simulating get_security_policies with mock Panorama data...")
    print(f"Parameters: vsys={vsys}, src_ip={src_ip}, service_port={service_port}")

    # Import the actual functions to test with mock data
    from tools.policies import (
        _normalize_entries, _load_objects, _policy_matches_ip,
        _policy_matches_service, _get_zone_for_ip_from_interfaces,
        _get_zone_from_interface_config, _get_interface_ip_networks,
        _resolve_referenced_objects
    )

    # Simulate the main logic
    policies = _normalize_entries(mock_policies_data.get("entry", []))
    print(f"Found {len(policies)} security policies")

    # Zone inference
    derived_src_zone = None
    if src_ip:
        # Mock the zone/interface lookups
        zones = _normalize_entries(mock_zones_data.get("entry", []))
        zone_interface_map = {}
        for zone in zones:
            zone_name = zone.get("@name")
            if zone_name:
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

        interfaces = _normalize_entries(mock_interfaces_data.get("entry", []))
        interface_networks = {}
        for interface in interfaces:
            if isinstance(interface, dict):
                interface_name = interface.get("@name")
                if interface_name:
                    networks = []
                    if "layer3" in interface and isinstance(interface["layer3"], dict):
                        layer3_config = interface["layer3"]
                        if "ip" in layer3_config and isinstance(layer3_config["ip"], dict):
                            ip_entries = _normalize_entries(layer3_config["ip"].get("entry", []))
                            for ip_entry in ip_entries:
                                if isinstance(ip_entry, dict) and "member" in ip_entry:
                                    ip_addr = ip_entry["member"]
                                    if "/" in ip_addr:
                                        try:
                                            import ipaddress
                                            network = ipaddress.ip_network(ip_addr, strict=False)
                                            networks.append(network)
                                        except ValueError:
                                            pass
                    if networks:
                        interface_networks[interface_name] = networks

        derived_src_zone = _get_zone_for_ip_from_interfaces(src_ip, zone_interface_map, interface_networks)

    print(f"Derived source zone for {src_ip}: {derived_src_zone}")

    # Filter policies
    filtered_policies = policies

    # Filter by derived zone
    if derived_src_zone:
        filtered_policies = [p for p in filtered_policies if p.get("from") == derived_src_zone]
        print(f"After zone filtering ({derived_src_zone}): {len(filtered_policies)} policies")

    # IP and service filtering would happen here with real address/service objects
    if src_ip or service_port:
        # Mock address and service maps
        address_map = {entry.get("@name"): entry for entry in _normalize_entries(mock_addresses_data.get("entry", [])) if entry.get("@name")}
        service_map = {entry.get("@name"): entry for entry in _normalize_entries(mock_services_data.get("entry", [])) if entry.get("@name")}

        filtered_policies = [
            p for p in filtered_policies
            if _policy_matches_ip(p, src_ip, address_map, {}, "source")
            and _policy_matches_service(p, service_port, service_map, {})
        ]
        print(f"After IP/service filtering: {len(filtered_policies)} policies")

    # Build result
    referenced_objects = _resolve_referenced_objects(filtered_policies, vsys)

    result = {
        "entry": filtered_policies,
        "referenced_objects": referenced_objects,
        "zone_inference": {
            "src_ip": src_ip,
            "derived_src_zone": derived_src_zone,
            "final_src_zone": derived_src_zone,
            "dst_ip": None,
            "derived_dst_zone": None,
            "final_dst_zone": None
        }
    }

    print("\nExpected MCP tool result:")
    print(json.dumps(result, indent=2))

    return result

if __name__ == "__main__":
    # Test the same parameters as the failing Azure call
    simulate_get_security_policies(
        vsys="vsys1",
        src_ip="10.137.0.0/24",
        service_port="443"
    )