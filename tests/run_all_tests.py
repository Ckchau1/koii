#!/usr/bin/env python3
"""
Master test runner for KOII OS.

Runs all test suites:
- Browser feature tests
- Semantic agent tests
- Integration tests
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_browser_features import BrowserFeatureTests
from tests.test_semantic_agent import SemanticAgentTests


async def main():
    """Run all test suites."""
    print("\n" + "🤖" * 30)
    print("KOII OS COMPREHENSIVE TEST SUITE")
    print("🤖" * 30)
    print("\nRunning all tests to validate enhancements...")
    print("This may take a few minutes.\n")
    
    total_passed = 0
    total_failed = 0
    
    try:
        # Run browser tests
        print("\n" + "=" * 60)
        print("PHASE 1: BROWSER FEATURES")
        print("=" * 60)
        
        browser_tests = BrowserFeatureTests()
        browser_success = await browser_tests.run_all_tests()
        total_passed += browser_tests.passed
        total_failed += browser_tests.failed
        
        # Run semantic agent tests
        print("\n" + "=" * 60)
        print("PHASE 2: SEMANTIC AGENT FEATURES")
        print("=" * 60)
        
        agent_tests = SemanticAgentTests()
        agent_success = await agent_tests.run_all_tests()
        total_passed += agent_tests.passed
        total_failed += agent_tests.failed
        
        # Final summary
        print("\n" + "=" * 60)
        print("🏁 FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"\n📊 Overall Results:")
        print(f"   ✅ Total Passed: {total_passed}")
        print(f"   ❌ Total Failed: {total_failed}")
        print(f"   📈 Success Rate: {(total_passed/(total_passed+total_failed)*100):.1f}%")
        
        print(f"\n🌐 Browser Tests: {'✅ PASSED' if browser_success else '❌ FAILED'}")
        print(f"🤖 Agent Tests: {'✅ PASSED' if agent_success else '❌ FAILED'}")
        
        if browser_success and agent_success:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED!")
            print("=" * 60)
            print("\n✅ KOII OS enhancements are fully validated!")
            print("✅ Native browser features working correctly")
            print("✅ Semantic agent dialogue features working correctly")
            print("✅ Ready for production deployment")
            print("\n🚀 You can now deploy with confidence using Docker:")
            print("   docker compose up -d")
            print("\n")
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("⚠️  SOME TESTS FAILED")
            print("=" * 60)
            print("\nPlease review the test output above for details.")
            print("Fix any issues before deploying to production.")
            print("\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n📝 Note: These tests require:")
    print("   - Python 3.11+")
    print("   - Playwright installed (pip install playwright)")
    print("   - Playwright browsers installed (playwright install chromium)")
    print("\n")
    
    asyncio.run(main())

# Made with Bob