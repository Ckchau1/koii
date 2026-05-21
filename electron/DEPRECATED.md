# DEPRECATED: Electron Min Browser

⚠️ **This directory is deprecated and will be removed in a future release.**

## Reason for Deprecation

The Electron-based Min Browser has been replaced by the Playwright-based AIBrowser which provides:

- ✅ **Better cross-platform support** - Works seamlessly on Windows, Linux, macOS via Docker
- ✅ **Native browser kernel** - Real Chromium engine with full JavaScript support
- ✅ **Enhanced capabilities** - Anti-scraping, CAPTCHA handling, session management
- ✅ **Simpler deployment** - No separate Electron process required
- ✅ **Lower resource usage** - More efficient than running separate Electron instances

## Migration Guide

### Old Code (Min Browser)
```python
from koii_os.browser.min_browser import MinBrowserController

browser = MinBrowserController()
await browser.start()
await browser.create_tab("https://example.com")
```

### New Code (AIBrowser)
```python
from koii_os.browser.engine import AIBrowser

browser = AIBrowser(headless=True)
await browser.start()
await browser.navigate("https://example.com")
```

## API Mapping

| Min Browser Method | AIBrowser Equivalent |
|-------------------|---------------------|
| `create_tab(url)` | `navigate(url)` |
| `click(selector, tab_id)` | `click(selector)` |
| `type(selector, text, tab_id)` | `type_text(selector, text)` |
| `get_text(tab_id)` | `get_text()` |
| `screenshot(tab_id)` | `screenshot()` |
| `execute(script, tab_id)` | `execute_js(script)` |

## Timeline

- **Current**: Deprecated, not recommended for new projects
- **6 months**: Will be removed from the codebase
- **Support**: Limited bug fixes only, no new features

## Questions?

See the main documentation:
- [Browser Features Guide](../BROWSER_FEATURES.md)
- [Implementation Plan](../IMPLEMENTATION_PLAN.md)
- [README](../README.md)

---

**Last Updated**: 2026-05-21