#!/usr/bin/env python3
"""
Debug script for testing Panorama MCP Server components
"""
import logging
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from app.config import PANORAMA_URL, KEYVAULT_URL
        print("✓ Config imported successfully")
        print(f"  Panorama URL: {PANORAMA_URL}")
        print(f"  Key Vault URL: {KEYVAULT_URL}")

        from app.keyvault_client import get_secret
        print("✓ Key Vault client imported successfully")

        from app.panorama_client import PanoramaClient
        print("✓ Panorama client imported successfully")

        from tools import threat, traffic, url
        print("✓ All tools imported successfully")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_keyvault():
    """Test Key Vault connectivity"""
    print("\nTesting Key Vault connectivity...")
    try:
        from app.keyvault_client import get_secret

        # Test retrieving Panorama credentials
        username = get_secret("panorama-username")
        password = get_secret("panorama-password")

        print("✓ Key Vault secrets retrieved successfully")
        print(f"  Username: {username[:3]}***")  # Show first 3 chars only
        return True
    except Exception as e:
        print(f"✗ Key Vault test failed: {e}")
        return False

def test_panorama_connection():
    """Test Panorama API connectivity"""
    print("\nTesting Panorama API connectivity...")
    print("⚠️  Note: SSL certificate verification is DISABLED for testing")
    try:
        from app.panorama_client import PanoramaClient

        client = PanoramaClient()
        # This will test API key generation
        api_key = client._generate_api_key()

        if api_key:
            print("✓ Panorama API key generated successfully")
            print(f"  API Key: {api_key[:10]}***")  # Show first 10 chars only
            return True
        else:
            print("✗ API key generation returned empty result")
            return False
    except Exception as e:
        print(f"✗ Panorama connection test failed: {e}")
        return False

def test_log_query():
    """Test a simple log query"""
    print("\nTesting log query (this may take a few seconds)...")
    try:
        from app.panorama_client import PanoramaClient

        client = PanoramaClient()
        # Test with a simple query that should return minimal results
        logs = client.query_logs("(addr.src in 127.0.0.1)", "traffic")

        print("✓ Log query completed successfully")
        if isinstance(logs, list):
            print(f"  Retrieved {len(logs)} log entries")
        else:
            print("  Retrieved 1 log entry (dict format)")

        return True
    except Exception as e:
        print(f"✗ Log query test failed: {e}")
        return False

def main():
    print("🔍 Panorama MCP Server Debug Script")
    print("=" * 50)

    # Run all tests
    tests = [
        ("Imports", test_imports),
        ("Key Vault", test_keyvault),
        ("Panorama Connection", test_panorama_connection),
        ("Log Query", test_log_query)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

def main():
    print("🔍 Palo Alto MCP Server Debug Script")
    print("=" * 50)

    # Run all tests
    tests = [
        ("Imports", test_imports),
        ("Key Vault", test_keyvault),
        ("Panorama Connection", test_panorama_connection),
        ("Log Query", test_log_query)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your MCP server should be ready to run.")
        print("\n🚀 Next steps:")
        print("  • Local development: python paloalto.py")
        print("  • HTTP server: python paloalto.py http")
        print("  • Test transports: python test_transports.py")
        print("  • Azure Functions: python azure_deploy.py")
    else:
        print("⚠️  Some tests failed. Check the error messages above for debugging.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()