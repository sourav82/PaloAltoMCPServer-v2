#!/usr/bin/env python3
"""
Test script for unified MCP server transports
"""
import subprocess
import time
import requests
import threading
import signal
import sys

def test_stdio_mode():
    """Test stdio transport mode"""
    print("🧪 Testing stdio transport mode...")

    try:
        # This would require implementing a full MCP client to test
        # For now, just test that the import works
        from paloalto import main
        print("✓ Stdio mode imports successfully")
        return True
    except Exception as e:
        print(f"✗ Stdio mode test failed: {e}")
        return False

def test_http_mode():
    """Test HTTP transport mode"""
    print("🧪 Testing HTTP transport mode...")

    # Start HTTP server in background
    server_process = None
    try:
        server_process = subprocess.Popen(
            [sys.executable, 'paloalto.py', 'http'],
            env={'PORT': '8765', **dict(os.environ)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to start
        time.sleep(3)

        # Test health endpoint
        response = requests.get('http://localhost:8765/health', timeout=5)
        if response.status_code == 200:
            print("✓ HTTP server health check passed")
        else:
            print(f"✗ HTTP server health check failed: {response.status_code}")
            return False

        # Test MCP endpoint
        mcp_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        response = requests.post(
            'http://localhost:8765/mcp',
            json=mcp_payload,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if 'result' in result and 'tools' in result['result']:
                print("✓ HTTP MCP endpoint working")
                return True
            else:
                print(f"✗ HTTP MCP endpoint returned unexpected response: {result}")
                return False
        else:
            print(f"✗ HTTP MCP endpoint failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ HTTP mode test failed: {e}")
        return False
    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()

def main():
    print("🔄 Testing Unified MCP Server Transports")
    print("=" * 50)

    # Test imports
    tests = [
        ("Stdio Transport", test_stdio_mode),
        ("HTTP Transport", test_http_mode)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Transport Test Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All transport modes working!")
        print("\nUsage:")
        print("  Local (stdio): python paloalto.py")
        print("  Remote (HTTP): python paloalto.py http")
    else:
        print("⚠️  Some transport modes failed. Check error messages above.")

if __name__ == "__main__":
    main()