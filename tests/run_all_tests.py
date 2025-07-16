#!/usr/bin/env python3
"""
Test runner to execute all tests in sequence
"""
import sys
import os
import subprocess
import time

# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test(test_name, test_file):
    """Run a single test and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {test_name} completed in {duration:.2f}s")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT - {test_name} timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ ERROR - {test_name} failed with error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running All Tests for Confluence AI Knowledge Base")
    print("=" * 60)
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    tests = [
        ("Cache Functionality", os.path.join(test_dir, "test_cache.py")),
        ("Vector Search", os.path.join(test_dir, "test_vector_search.py")),
        ("End-to-End Functionality", os.path.join(test_dir, "test_end_to_end.py")),
        ("Confluence Sync", os.path.join(test_dir, "test_sync_confluence.py")),
    ]
    
    results = {}
    start_time = time.time()
    
    for test_name, test_file in tests:
        if os.path.exists(test_file):
            results[test_name] = run_test(test_name, test_file)
        else:
            print(f"❌ Test file not found: {test_file}")
            results[test_name] = False
    
    total_time = time.time() - start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    print(f"Total execution time: {total_time:.2f}s")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())