#!/usr/bin/env python3
"""
Test suite for enhanced AIBrowser features.

Tests:
- Stealth mode and anti-detection
- CAPTCHA detection
- Dynamic content handling
- Session management
- Request interception
- Infinite scroll
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.koii_os.browser.engine import AIBrowser


class BrowserFeatureTests:
    """Test suite for browser features."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    async def test_stealth_mode(self):
        """Test stealth mode initialization."""
        print("\n🥷 Test 1: Stealth Mode")
        print("-" * 50)
        
        try:
            browser = AIBrowser(stealth_mode=True, headless=True)
            await browser.start()
            
            # Navigate to a test page
            result = await browser.navigate("https://example.com")
            
            assert result['status'] == 'ok', "Navigation failed"
            assert result['url'] == "https://example.com/", "URL mismatch"
            
            # Check if stealth scripts were applied
            webdriver_check = await browser.execute_js("return navigator.webdriver")
            assert webdriver_check['result'] is None, "Webdriver flag not hidden"
            
            await browser.stop()
            
            print("✅ PASSED: Stealth mode working")
            print(f"   - Navigation successful")
            print(f"   - Webdriver flag hidden")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_captcha_detection(self):
        """Test CAPTCHA detection capability."""
        print("\n🔐 Test 2: CAPTCHA Detection")
        print("-" * 50)
        
        try:
            browser = AIBrowser(stealth_mode=True, headless=True)
            await browser.start()
            
            # Navigate to example page (no CAPTCHA expected)
            await browser.navigate("https://example.com")
            
            # Test CAPTCHA detection
            captcha_result = await browser.detect_captcha()
            
            assert 'detected' in captcha_result, "Missing 'detected' field"
            assert 'type' in captcha_result, "Missing 'type' field"
            assert captcha_result['detected'] == False, "False positive CAPTCHA detection"
            
            await browser.stop()
            
            print("✅ PASSED: CAPTCHA detection working")
            print(f"   - Detection method functional")
            print(f"   - No false positives on clean page")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_dynamic_content(self):
        """Test dynamic content waiting."""
        print("\n⚡ Test 3: Dynamic Content Handling")
        print("-" * 50)
        
        try:
            browser = AIBrowser(stealth_mode=True, headless=True)
            await browser.start()
            
            # Navigate and wait for network idle
            await browser.navigate("https://example.com")
            
            result = await browser.wait_for_dynamic_content(
                wait_for="networkidle",
                timeout=10000
            )
            
            assert result['status'] == 'ok', "Dynamic content wait failed"
            assert 'load_time_ms' in result, "Missing load time"
            assert result['load_time_ms'] > 0, "Invalid load time"
            
            await browser.stop()
            
            print("✅ PASSED: Dynamic content handling working")
            print(f"   - Network idle detection functional")
            print(f"   - Load time: {result['load_time_ms']:.0f}ms")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_session_management(self):
        """Test session save and load."""
        print("\n💾 Test 4: Session Management")
        print("-" * 50)
        
        try:
            browser = AIBrowser(stealth_mode=True, headless=True)
            await browser.start()
            
            # Navigate to create some session data
            await browser.navigate("https://example.com")
            
            # Save session
            save_result = await browser.save_session("test_session")
            
            assert save_result['status'] == 'ok', "Session save failed"
            assert 'session_name' in save_result, "Missing session name"
            assert save_result['session_name'] == "test_session", "Session name mismatch"
            
            # Load session
            load_result = await browser.load_session("test_session")
            
            assert load_result['status'] == 'ok', "Session load failed"
            assert 'restored_cookies' in load_result, "Missing restored cookies count"
            
            await browser.stop()
            
            print("✅ PASSED: Session management working")
            print(f"   - Session saved successfully")
            print(f"   - Session loaded successfully")
            print(f"   - Cookies: {save_result.get('cookies_count', 0)}")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_request_interception(self):
        """Test request interception."""
        print("\n🚫 Test 5: Request Interception")
        print("-" * 50)
        
        try:
            browser = AIBrowser(stealth_mode=True, headless=True)
            await browser.start()
            
            # Set up request interception
            result = await browser.intercept_requests(
                patterns=["**/ads/*", "**/tracking/*"],
                block=True
            )
            
            assert result['status'] == 'ok', "Request interception setup failed"
            assert 'patterns' in result, "Missing patterns"
            assert len(result['patterns']) == 2, "Pattern count mismatch"
            
            # Navigate to test interception
            await browser.navigate("https://example.com")
            
            await browser.stop()
            
            print("✅ PASSED: Request interception working")
            print(f"   - Interception configured")
            print(f"   - Patterns: {result['patterns']}")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_script_injection(self):
        """Test custom script injection."""
        print("\n💉 Test 6: Script Injection")
        print("-" * 50)
        
        try:
            browser = AIBrowser(stealth_mode=True, headless=True)
            await browser.start()
            
            await browser.navigate("https://example.com")
            
            # Inject custom scripts
            scripts = [
                "return document.title",
                "return window.location.href"
            ]
            
            result = await browser.inject_scripts(scripts)
            
            assert result['status'] == 'ok', "Script injection failed"
            assert 'scripts_executed' in result, "Missing execution count"
            assert result['scripts_executed'] == 2, "Script count mismatch"
            assert len(result['results']) == 2, "Results count mismatch"
            
            await browser.stop()
            
            print("✅ PASSED: Script injection working")
            print(f"   - Scripts executed: {result['scripts_executed']}")
            print(f"   - Results: {result['results']}")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def test_infinite_scroll(self):
        """Test infinite scroll handling."""
        print("\n📜 Test 7: Infinite Scroll Handling")
        print("-" * 50)
        
        try:
            browser = AIBrowser(stealth_mode=True, headless=True)
            await browser.start()
            
            await browser.navigate("https://example.com")
            
            # Test scroll handling
            result = await browser.handle_infinite_scroll(
                max_scrolls=3,
                scroll_delay=0.5
            )
            
            assert result['status'] == 'ok', "Infinite scroll failed"
            assert 'scrolls_performed' in result, "Missing scroll count"
            assert result['scrolls_performed'] >= 0, "Invalid scroll count"
            
            await browser.stop()
            
            print("✅ PASSED: Infinite scroll handling working")
            print(f"   - Scrolls performed: {result['scrolls_performed']}")
            print(f"   - Final height: {result.get('final_height', 0)}px")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.failed += 1
            return False
    
    async def run_all_tests(self):
        """Run all browser feature tests."""
        print("\n" + "=" * 60)
        print("🌐 BROWSER FEATURE TEST SUITE")
        print("=" * 60)
        print("\nTesting enhanced AIBrowser capabilities...")
        print("This validates: stealth mode, CAPTCHA, sessions, etc.")
        
        # Run all tests
        await self.test_stealth_mode()
        await self.test_captcha_detection()
        await self.test_dynamic_content()
        await self.test_session_management()
        await self.test_request_interception()
        await self.test_script_injection()
        await self.test_infinite_scroll()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        print("=" * 60)
        
        return self.failed == 0


async def main():
    """Run browser feature tests."""
    try:
        tests = BrowserFeatureTests()
        success = await tests.run_all_tests()
        
        if success:
            print("\n🎉 All browser tests passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Review output above.")
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
    asyncio.run(main())

# Made with Bob