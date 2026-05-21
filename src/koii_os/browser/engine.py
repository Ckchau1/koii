from __future__ import annotations

import asyncio
import base64
import json
import os
import time
import random
from pathlib import Path
from typing import Any, Optional, Dict, List


class AIBrowser:
    """
    Native Chromium-based browser controlled by AI agents via Playwright.
    
    Features:
    - Real browser kernel (not simulated)
    - Anti-scraping & bot detection evasion
    - CAPTCHA detection and handling
    - Dynamic JavaScript loading support
    - Session management (cookies, storage)
    - Request interception
    - Cross-platform (Windows, Linux, macOS via Docker)
    
    Runs directly on the real browser kernel, perfectly handling:
    - Dynamic JavaScript loading
    - Anti-scraping mechanisms
    - CAPTCHA challenges
    - Real-time context with low latency
    - Higher privacy and security
    """

    def __init__(
        self,
        headless: bool = True,
        screenshot_dir: str = "./data/screenshots",
        stealth_mode: bool = True,
        user_agent: Optional[str] = None
    ) -> None:
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.stealth_mode = stealth_mode
        self.custom_user_agent = user_agent
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None
        self._playwright: Any = None
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._request_interceptors: List[Any] = []

    async def start(self) -> None:
        """Start browser with stealth mode and anti-detection features."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        
        # Enhanced launch args for stealth and performance
        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",  # Hide automation
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-web-security",  # For testing, remove in production
        ]
        
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
        )
        
        # Randomize viewport for stealth
        viewport_width = random.randint(1280, 1920)
        viewport_height = random.randint(720, 1080)
        
        # Realistic user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        user_agent = self.custom_user_agent or random.choice(user_agents)
        
        self._context = await self._browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=user_agent,
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation", "notifications"],
        )
        
        self._page = await self._context.new_page()
        
        # Apply stealth mode if enabled
        if self.stealth_mode:
            await self._apply_stealth_mode()
    
    async def _apply_stealth_mode(self) -> None:
        """Apply stealth scripts to avoid bot detection."""
        if not self._page:
            return
        
        # Inject stealth scripts
        stealth_js = """
        // Override navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Override chrome property
        window.chrome = {
            runtime: {}
        };
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Add realistic screen properties
        Object.defineProperty(screen, 'availWidth', {
            get: () => window.innerWidth
        });
        Object.defineProperty(screen, 'availHeight', {
            get: () => window.innerHeight
        });
        """
        
        await self._page.add_init_script(stealth_js)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None

    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        if not self._page:
            await self.start()
        try:
            response = await self._page.goto(url, wait_until=wait_until, timeout=30_000)
            return {
                "status": "ok",
                "url": self._page.url,
                "status_code": response.status if response else None,
                "title": await self._page.title(),
            }
        except Exception as e:
            return {"status": "error", "reason": str(e), "url": url}

    async def screenshot(self, label: str = "") -> dict[str, Any]:
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            ts = int(time.time() * 1000)
            fname = f"{ts}_{label}.png" if label else f"{ts}.png"
            fpath = self.screenshot_dir / fname
            await self._page.screenshot(path=str(fpath), full_page=False)
            # Also return base64 for inline use
            img_bytes = fpath.read_bytes()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            return {
                "status": "ok",
                "path": str(fpath),
                "base64": b64,
                "url": self._page.url,
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def get_text(self) -> dict[str, Any]:
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            text = await self._page.inner_text("body")
            return {
                "status": "ok",
                "text": text[:8000],
                "url": self._page.url,
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def get_links(self) -> dict[str, Any]:
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            links = await self._page.eval_on_selector_all(
                "a[href]",
                "els => els.map(el => ({ text: el.innerText.trim(), href: el.href }))",
            )
            return {"status": "ok", "links": links[:50], "url": self._page.url}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def click(self, selector: str | None = None, text: str | None = None) -> dict[str, Any]:
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            if text:
                await self._page.get_by_text(text, exact=False).first.click(timeout=10_000)
            elif selector:
                await self._page.click(selector, timeout=10_000)
            else:
                return {"status": "error", "reason": "provide selector or text"}
            await self._page.wait_for_load_state("domcontentloaded", timeout=10_000)
            return {"status": "ok", "url": self._page.url}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def type_text(self, selector: str, text: str, clear_first: bool = True) -> dict[str, Any]:
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            await self._page.click(selector, timeout=10_000)
            if clear_first:
                await self._page.fill(selector, "")
            await self._page.type(selector, text, delay=30)
            return {"status": "ok", "selector": selector, "typed": text}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def press_key(self, key: str) -> dict[str, Any]:
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            await self._page.keyboard.press(key)
            await asyncio.sleep(0.5)
            return {"status": "ok", "key": key, "url": self._page.url}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def execute_js(self, script: str) -> dict[str, Any]:
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            result = await self._page.evaluate(script)
            return {"status": "ok", "result": result}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def get_dom_snapshot(self) -> dict[str, Any]:
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            html = await self._page.content()
            return {
                "status": "ok",
                "html": html[:16000],
                "url": self._page.url,
                "title": await self._page.title(),
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def find_elements(self, description: str) -> dict[str, Any]:
        """Extract interactive elements relevant to the given description."""
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        try:
            elements = await self._page.evaluate("""() => {
                const interactive = [];
                document.querySelectorAll('button, input, select, textarea, a[href], [role="button"], [onclick]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        interactive.push({
                            tag: el.tagName.toLowerCase(),
                            type: el.type || null,
                            text: (el.innerText || el.value || el.placeholder || el.alt || '').trim().substring(0, 80),
                            id: el.id || null,
                            name: el.name || null,
                            href: el.href || null,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                        });
                    }
                });
                return interactive.slice(0, 30);
            }""")
            return {"status": "ok", "elements": elements, "url": self._page.url}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def run_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a structured action dict (from LLM planner)."""
        act = action.get("action", "")
        if act == "navigate":
            return await self.navigate(str(action.get("url", "")))
        if act == "click":
            return await self.click(
                selector=action.get("selector"),
                text=action.get("text"),
            )
        if act == "type":
            return await self.type_text(
                selector=str(action.get("selector", "")),
                text=str(action.get("text", "")),
                clear_first=bool(action.get("clear_first", True)),
            )
        if act == "press":
            return await self.press_key(str(action.get("key", "Enter")))
        if act == "screenshot":
            return await self.screenshot(str(action.get("label", "")))
        if act == "get_text":
            return await self.get_text()
        if act == "get_links":
            return await self.get_links()
        if act == "get_elements":
            return await self.find_elements(str(action.get("description", "")))
        if act == "execute_js":
            return await self.execute_js(str(action.get("script", "")))
        if act == "dom_snapshot":
            return await self.get_dom_snapshot()
        return {"status": "error", "reason": f"unknown action: {act}"}

    @property
    def current_url(self) -> str:
        return self._page.url if self._page else ""

    
    async def detect_captcha(self) -> dict[str, Any]:
        """
        Detect if there's a CAPTCHA on the current page.
        
        Returns:
            dict with 'detected': bool, 'type': str (recaptcha, hcaptcha, etc.)
        """
        if not self._page:
            return {"detected": False, "type": None}
        
        try:
            # Check for common CAPTCHA elements
            captcha_selectors = {
                "recaptcha": "iframe[src*='recaptcha']",
                "hcaptcha": "iframe[src*='hcaptcha']",
                "cloudflare": ".cf-challenge-running",
                "generic": "[class*='captcha'], [id*='captcha']"
            }
            
            for captcha_type, selector in captcha_selectors.items():
                element = await self._page.query_selector(selector)
                if element:
                    return {
                        "detected": True,
                        "type": captcha_type,
                        "message": f"Detected {captcha_type} CAPTCHA"
                    }
            
            return {"detected": False, "type": None}
        except Exception as e:
            return {"detected": False, "type": None, "error": str(e)}
    
    async def wait_for_captcha_solve(self, timeout: int = 120000) -> dict[str, Any]:
        """
        Wait for CAPTCHA to be solved (either manually or via service).
        
        Args:
            timeout: Maximum time to wait in milliseconds
        
        Returns:
            dict with 'solved': bool, 'method': str
        """
        if not self._page:
            return {"solved": False, "reason": "browser not started"}
        
        try:
            start_time = time.time()
            while (time.time() - start_time) * 1000 < timeout:
                captcha_status = await self.detect_captcha()
                if not captcha_status["detected"]:
                    return {
                        "solved": True,
                        "method": "manual_or_automatic",
                        "time_taken": (time.time() - start_time)
                    }
                await asyncio.sleep(2)
            
            return {"solved": False, "reason": "timeout"}
        except Exception as e:
            return {"solved": False, "reason": str(e)}
    
    async def wait_for_dynamic_content(
        self,
        selector: Optional[str] = None,
        timeout: int = 30000,
        wait_for: str = "networkidle"
    ) -> dict[str, Any]:
        """
        Wait for dynamically loaded content.
        
        Args:
            selector: Optional CSS selector to wait for
            timeout: Maximum wait time in milliseconds
            wait_for: 'networkidle', 'load', or 'domcontentloaded'
        
        Returns:
            dict with status and timing information
        """
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        
        try:
            start_time = time.time()
            
            # Wait for network to be idle
            if wait_for == "networkidle":
                await self._page.wait_for_load_state("networkidle", timeout=timeout)
            elif wait_for == "load":
                await self._page.wait_for_load_state("load", timeout=timeout)
            else:
                await self._page.wait_for_load_state("domcontentloaded", timeout=timeout)
            
            # If selector provided, wait for it
            if selector:
                await self._page.wait_for_selector(selector, timeout=timeout)
            
            load_time = (time.time() - start_time) * 1000
            
            return {
                "status": "ok",
                "load_time_ms": load_time,
                "url": self._page.url
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    async def save_session(self, session_name: str) -> dict[str, Any]:
        """
        Save current browser session (cookies, storage, etc.).
        
        Args:
            session_name: Name to identify this session
        
        Returns:
            dict with status and session info
        """
        if not self._context:
            return {"status": "error", "reason": "browser not started"}
        
        try:
            # Get cookies
            cookies = await self._context.cookies()
            
            # Get local storage (requires page evaluation)
            local_storage = {}
            if self._page:
                local_storage = await self._page.evaluate("""() => {
                    let storage = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }
                    return storage;
                }""")
            
            # Save session
            self._sessions[session_name] = {
                "cookies": cookies,
                "local_storage": local_storage,
                "timestamp": time.time(),
                "url": self._page.url if self._page else None
            }
            
            # Optionally save to file
            session_file = self.screenshot_dir.parent / "sessions" / f"{session_name}.json"
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(session_file, "w") as f:
                json.dump(self._sessions[session_name], f, indent=2)
            
            return {
                "status": "ok",
                "session_name": session_name,
                "cookies_count": len(cookies),
                "storage_keys": len(local_storage),
                "file": str(session_file)
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    async def load_session(self, session_name: str) -> dict[str, Any]:
        """
        Load a previously saved session.
        
        Args:
            session_name: Name of the session to load
        
        Returns:
            dict with status
        """
        if not self._context:
            return {"status": "error", "reason": "browser not started"}
        
        try:
            # Try to load from memory first
            session_data = self._sessions.get(session_name)
            
            # If not in memory, try to load from file
            if not session_data:
                session_file = self.screenshot_dir.parent / "sessions" / f"{session_name}.json"
                if session_file.exists():
                    with open(session_file, "r") as f:
                        session_data = json.load(f)
                else:
                    return {"status": "error", "reason": f"session '{session_name}' not found"}
            
            # Restore cookies
            if session_data.get("cookies"):
                await self._context.add_cookies(session_data["cookies"])
            
            # Restore local storage (requires navigation to a page first)
            if session_data.get("local_storage") and self._page:
                # Navigate to the saved URL or a blank page
                url = session_data.get("url") or "about:blank"
                await self._page.goto(url)
                
                # Inject local storage
                for key, value in session_data["local_storage"].items():
                    await self._page.evaluate(
                        f"localStorage.setItem('{key}', '{value}')"
                    )
            
            return {
                "status": "ok",
                "session_name": session_name,
                "restored_cookies": len(session_data.get("cookies", [])),
                "restored_storage": len(session_data.get("local_storage", {}))
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    async def intercept_requests(
        self,
        patterns: List[str],
        block: bool = True
    ) -> dict[str, Any]:
        """
        Intercept and optionally block network requests matching patterns.
        
        Args:
            patterns: List of URL patterns to intercept (supports wildcards)
            block: Whether to block matching requests
        
        Returns:
            dict with status
        """
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        
        try:
            async def handle_route(route, request):
                # Check if request URL matches any pattern
                url = request.url
                should_block = any(
                    pattern in url or url.startswith(pattern)
                    for pattern in patterns
                )
                
                if should_block and block:
                    await route.abort()
                else:
                    await route.continue_()
            
            # Register route handler
            await self._page.route("**/*", handle_route)
            
            return {
                "status": "ok",
                "patterns": patterns,
                "action": "block" if block else "log"
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    async def inject_scripts(self, scripts: List[str]) -> dict[str, Any]:
        """
        Inject custom JavaScript scripts into the page.
        
        Args:
            scripts: List of JavaScript code strings to inject
        
        Returns:
            dict with status and results
        """
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        
        try:
            results = []
            for script in scripts:
                result = await self._page.evaluate(script)
                results.append(result)
            
            return {
                "status": "ok",
                "scripts_executed": len(scripts),
                "results": results
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    async def handle_infinite_scroll(
        self,
        max_scrolls: int = 10,
        scroll_delay: float = 1.0
    ) -> dict[str, Any]:
        """
        Handle infinite scroll pages by scrolling to bottom multiple times.
        
        Args:
            max_scrolls: Maximum number of scroll attempts
            scroll_delay: Delay between scrolls in seconds
        
        Returns:
            dict with status and scroll count
        """
        if not self._page:
            return {"status": "error", "reason": "browser not started"}
        
        try:
            scroll_count = 0
            previous_height = 0
            
            for i in range(max_scrolls):
                # Get current scroll height
                current_height = await self._page.evaluate("document.body.scrollHeight")
                
                # If height hasn't changed, we've reached the end
                if current_height == previous_height and i > 0:
                    break
                
                # Scroll to bottom
                await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(scroll_delay)
                
                previous_height = current_height
                scroll_count += 1
            
            return {
                "status": "ok",
                "scrolls_performed": scroll_count,
                "final_height": previous_height
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
