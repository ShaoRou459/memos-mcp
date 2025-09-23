#!/usr/bin/env python3
"""Test script for MCP Memos Server."""

import asyncio
import os
import sys
from datetime import date
from typing import Dict, Any

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config, validate_config, MemosConfig
from memos_client import MemosClient, MemosAPIError


class TestRunner:
    """Test runner for MCP Memos Server."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    def test(self, name: str, condition: bool, message: str = ""):
        """Run a test and track results."""
        if condition:
            print(f"✅ PASS: {name}")
            self.passed += 1
        else:
            print(f"❌ FAIL: {name} - {message}")
            self.failed += 1
    
    def skip(self, name: str, reason: str):
        """Skip a test."""
        print(f"⏭️ SKIP: {name} - {reason}")
        self.skipped += 1
    
    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed + self.skipped
        print(f"\n{'='*50}")
        print(f"Test Summary:")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        print(f"  Skipped: {self.skipped}")
        print(f"  Total: {total}")
        print(f"{'='*50}")
        
        if self.failed == 0:
            print("🎉 All tests passed!")
            return True
        else:
            print("💥 Some tests failed!")
            return False


async def test_configuration():
    """Test configuration loading and validation."""
    test = TestRunner()
    
    print("Testing Configuration...")
    
    # Test config loading
    try:
        config = get_config()
        test.test("Config loading", True)
    except Exception as e:
        test.test("Config loading", False, str(e))
        return test
    
    # Test config validation
    is_valid = validate_config()
    if not is_valid:
        test.skip("Config validation", "Missing MEMOS_URL or MEMOS_API_KEY environment variables")
        return test
    else:
        test.test("Config validation", True)
    
    # Test required fields
    test.test("MEMOS_URL present", bool(config.memos_url))
    test.test("MEMOS_API_KEY present", bool(config.memos_api_key))
    
    # Test optional fields have defaults
    test.test("Default visibility set", config.default_visibility in ["PRIVATE", "PROTECTED", "PUBLIC"])
    test.test("Max search results is positive", config.max_search_results > 0)
    test.test("Timeout is positive", config.timeout > 0)
    
    return test


async def test_memos_client():
    """Test Memos client functionality."""
    test = TestRunner()
    
    print("\nTesting Memos Client...")
    
    # Check if we have valid config
    if not validate_config():
        test.skip("All client tests", "Configuration not valid")
        return test
    
    config = get_config()
    
    try:
        async with MemosClient(config) as client:
            # Test connection by trying to list memos
            try:
                response = await client.list_memos(limit=1)
                test.test("Connection to Memos server", True)
                
                # Test response structure
                test.test("Response has memos key", "memos" in response)
                
                # If we have memos, test one
                memos = response.get("memos", [])
                if memos:
                    memo = memos[0]
                    test.test("Memo has content", "content" in memo)
                    test.test("Memo has createTime", "createTime" in memo)
                    test.test("Memo has name (ID)", "name" in memo)
                else:
                    test.skip("Memo structure tests", "No memos found in account")
                
            except MemosAPIError as e:
                test.test("Connection to Memos server", False, str(e))
                test.skip("Response structure tests", "Connection failed")
    
    except Exception as e:
        test.test("Client initialization", False, str(e))
        test.skip("All other client tests", "Client init failed")
    
    return test


async def test_search_functionality():
    """Test search and filtering functionality."""
    test = TestRunner()
    
    print("\nTesting Search Functionality...")
    
    if not validate_config():
        test.skip("All search tests", "Configuration not valid")
        return test
    
    config = get_config()
    
    try:
        async with MemosClient(config) as client:
            # Test search (even if no results)
            try:
                results = await client.search_memos("test", limit=5)
                test.test("Search execution", True)
                test.test("Search returns list", isinstance(results, list))
            except Exception as e:
                test.test("Search execution", False, str(e))
            
            # Test date filtering
            try:
                today = date.today()
                results = await client.get_memos_by_date(today, limit=5)
                test.test("Date filtering execution", True)
                test.test("Date filtering returns list", isinstance(results, list))
            except Exception as e:
                test.test("Date filtering execution", False, str(e))
            
            # Test recent memos
            try:
                results = await client.get_recent_memos(limit=5)
                test.test("Recent memos execution", True)
                test.test("Recent memos returns list", isinstance(results, list))
            except Exception as e:
                test.test("Recent memos execution", False, str(e))
    
    except Exception as e:
        test.skip("All search tests", f"Client error: {e}")
    
    return test


async def test_integration():
    """Test full integration if possible (requires write permissions)."""
    test = TestRunner()
    
    print("\nTesting Integration (Create/Update/Delete)...")
    
    if not validate_config():
        test.skip("All integration tests", "Configuration not valid")
        return test
    
    config = get_config()
    test_memo_content = "🧪 Test memo created by MCP server test - safe to delete"
    created_memo_id = None
    
    try:
        async with MemosClient(config) as client:
            # Test create memo
            try:
                result = await client.create_memo(test_memo_content, "PRIVATE")
                created_memo_id = result.get("name")
                test.test("Create memo", bool(created_memo_id))
            except MemosAPIError as e:
                test.test("Create memo", False, f"API Error: {e}")
                return test
            except Exception as e:
                test.test("Create memo", False, f"Error: {e}")
                return test
            
            # Test get memo
            if created_memo_id:
                try:
                    memo = await client.get_memo(created_memo_id)
                    test.test("Get memo", "content" in memo)
                    test.test("Memo content matches", test_memo_content in memo.get("content", ""))
                except Exception as e:
                    test.test("Get memo", False, str(e))
            
            # Test update memo
            if created_memo_id:
                try:
                    updated_content = test_memo_content + " - UPDATED"
                    await client.update_memo(created_memo_id, updated_content)
                    
                    # Verify update
                    updated_memo = await client.get_memo(created_memo_id)
                    test.test("Update memo", "UPDATED" in updated_memo.get("content", ""))
                except Exception as e:
                    test.test("Update memo", False, str(e))
            
            # Test delete memo (cleanup)
            if created_memo_id:
                try:
                    await client.delete_memo(created_memo_id)
                    test.test("Delete memo", True)
                    
                    # Verify deletion
                    try:
                        await client.get_memo(created_memo_id)
                        test.test("Memo actually deleted", False, "Memo still exists after deletion")
                    except MemosAPIError:
                        test.test("Memo actually deleted", True)
                except Exception as e:
                    test.test("Delete memo", False, str(e))
                    print(f"⚠️ Warning: Test memo {created_memo_id} may still exist")
    
    except Exception as e:
        test.skip("All integration tests", f"Client error: {e}")
        if created_memo_id:
            print(f"⚠️ Warning: Test memo {created_memo_id} may still exist")
    
    return test


def check_environment():
    """Check environment setup."""
    print("Checking Environment...")
    
    required_vars = ["MEMOS_URL", "MEMOS_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nTo run tests, set these environment variables:")
        for var in missing_vars:
            print(f"  export {var}='your_value_here'")
        print("\nOr create a .env file with these values.")
        return False
    
    print("✅ All required environment variables are set")
    return True


async def main():
    """Run all tests."""
    print("🧪 MCP Memos Server Test Suite")
    print("=" * 50)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please set required variables and try again.")
        sys.exit(1)
    
    # Run all test suites
    results = []
    
    results.append(await test_configuration())
    results.append(await test_memos_client())
    results.append(await test_search_functionality())
    
    # Only run integration tests if previous tests pass
    if all(r.failed == 0 for r in results):
        print("\n⚠️ Running integration tests (will create/update/delete a test memo)...")
        response = input("Continue? [y/N]: ").lower().strip()
        if response == 'y':
            results.append(await test_integration())
        else:
            print("Skipping integration tests.")
    else:
        print("\n⏭️ Skipping integration tests due to previous failures.")
    
    # Overall summary
    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)
    total_skipped = sum(r.skipped for r in results)
    
    print(f"\n{'='*50}")
    print("OVERALL TEST SUMMARY")
    print(f"{'='*50}")
    print(f"  Total Passed: {total_passed}")
    print(f"  Total Failed: {total_failed}")
    print(f"  Total Skipped: {total_skipped}")
    print(f"{'='*50}")
    
    if total_failed == 0:
        print("🎉 All tests completed successfully!")
        print("Your MCP Memos Server is ready to use!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        print("Please check the error messages above and fix any issues.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())