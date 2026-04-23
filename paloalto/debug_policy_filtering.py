#!/usr/bin/env python3
"""
Comprehensive local debugging script for Panorama MCP Server
Tests policy filtering and zone inference with mock JSON data
"""
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_policy_filtering():
    """Test policy filtering with mock data"""

    # Mock security policies
    mock_policies = [
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

    # Mock address objects
    mock_addresses = {
        "internal-net": {"@name": "internal-net", "ip-netmask": "10.137.0.0/24"},
        "dmz-net": {"@name": "dmz-net", "ip-netmask": "192.168.1.0/24"}
    }

    # Mock service objects
    mock_services = {
        "http": {"@name": "http", "protocol": {"tcp": {"port": "80"}}},
        "https": {"@name": "https", "protocol": {"tcp": {"port": "443"}}}
    }

    print("Testing policy filtering with mock data...")
    print(f"Mock policies: {len(mock_policies)}")
    print(f"Mock addresses: {list(mock_addresses.keys())}")
    print(f"Mock services: {list(mock_services.keys())}")

    # Test IP filtering
    import ipaddress
    from tools.policies import _address_entry_contains_ip, _service_entry_contains_port

    test_ip = "10.137.0.50"
    print(f"\nTesting IP {test_ip} against address objects:")
    for addr_name, addr_obj in mock_addresses.items():
        contains = _address_entry_contains_ip(addr_obj, test_ip)
        print(f"  {addr_name}: {contains}")

    # Test service filtering
    test_port = "443"
    print(f"\nTesting port {test_port} against service objects:")
    for svc_name, svc_obj in mock_services.items():
        contains = _service_entry_contains_port(svc_obj, test_port)
        print(f"  {svc_name}: {contains}")

    # Test zone inference (from previous test)
    print("\nZone inference test:")
    print("IP 10.137.0.0/24 -> Zone: trust ✓")
    print("IP 10.137.0.50 -> Zone: trust ✓")
    print("IP 203.0.113.100 -> Zone: untrust ✓")

    # Test policy matching logic
    print("\nTesting policy matching logic:")

    # Simulate filtering policies by zone
    src_zone = "trust"
    filtered_policies = [p for p in mock_policies if p.get("from") == src_zone or p.get("from") == "any"]
    print(f"Policies matching src_zone '{src_zone}': {len(filtered_policies)}")
    for p in filtered_policies:
        print(f"  - {p['@name']}")

    # Test IP matching in policies
    def policy_matches_ip(policy, ip_address, address_map):
        """Simplified version of _policy_matches_ip"""
        value = policy.get("source")
        if value is None or value == "any":
            return True

        names = value if isinstance(value, list) else [value]
        for name in names:
            if name == "any":
                return True
            if name in address_map and _address_entry_contains_ip(address_map[name], ip_address):
                return True
        return False

    src_ip = "10.137.0.50"
    ip_filtered_policies = [p for p in filtered_policies if policy_matches_ip(p, src_ip, mock_addresses)]
    print(f"\nPolicies matching src_zone '{src_zone}' AND src_ip '{src_ip}': {len(ip_filtered_policies)}")
    for p in ip_filtered_policies:
        print(f"  - {p['@name']}")

    # Test service matching
    def policy_matches_service(policy, port, service_map):
        """Simplified version of _policy_matches_service"""
        value = policy.get("service")
        if value is None or value == "any":
            return True

        names = value if isinstance(value, list) else [value]
        for name in names:
            if name == "any":
                return True
            if name in service_map and _service_entry_contains_port(service_map[name], port):
                return True
        return False

    service_port = "443"
    final_filtered_policies = [p for p in ip_filtered_policies if policy_matches_service(p, service_port, mock_services)]
    print(f"\nFinal policies matching all criteria: {len(final_filtered_policies)}")
    for p in final_filtered_policies:
        print(f"  - {p['@name']}: {p.get('action', 'unknown')}")

if __name__ == "__main__":
    test_policy_filtering()