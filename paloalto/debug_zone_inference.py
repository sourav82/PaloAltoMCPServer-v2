#!/usr/bin/env python3
"""
Local debugging script for Panorama MCP Server zone inference
Tests the zone inference logic with mock JSON data
"""
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.policies import (
    _get_zone_for_ip_from_interfaces,
    _get_zone_from_interface_config,
    _get_interface_ip_networks,
    _normalize_entries
)

def test_zone_inference():
    """Test zone inference with mock data"""

    # Mock zone configuration data (what would come from Panorama API)
    mock_zone_data = {
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

    # Mock interface configuration data
    mock_interface_data = {
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

    print("Testing zone inference with mock data...")

    # Parse the mock data as the functions would
    zones = _normalize_entries(mock_zone_data.get("entry", []))
    zone_interface_map = {}
    for zone in zones:
        zone_name = zone.get("@name")
        if not zone_name:
            continue

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

    print(f"Zone to interface mapping: {zone_interface_map}")

    # Parse interface IP networks
    interface_networks = {}
    interfaces = _normalize_entries(mock_interface_data.get("entry", []))
    for interface in interfaces:
        if not isinstance(interface, dict):
            continue

        interface_name = interface.get("@name")
        if not interface_name:
            continue

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
                            except ValueError as e:
                                print(f"Invalid IP network {ip_addr}: {e}")

        if networks:
            interface_networks[interface_name] = networks

    print(f"Interface to network mapping: {interface_networks}")

    # Test IP zone lookup
    test_ips = ["10.137.0.0/24", "10.137.0.50", "203.0.113.100", "192.168.1.1"]

    for ip in test_ips:
        zone = _get_zone_for_ip_from_interfaces(ip, zone_interface_map, interface_networks)
        print(f"IP {ip} -> Zone: {zone}")

if __name__ == "__main__":
    test_zone_inference()