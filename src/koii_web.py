from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import uvicorn

# Ensure imports work
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    from src.koii_os.api import app, set_runtime_context, setup_static_files
    from src.koii_cli import _build_runtime, _repo_root
    from src.koii_os.browser.engine import AIBrowser
    from src.koii_os.llm.registry import build_llm_registry_from_settings
    from src.koii_os.config.loader import load_config

    config = {}
    try:
        config = load_config(_repo_root() / "agent-config.yaml")
    except Exception:
        pass

    runtime_ctx = _build_runtime(config)

    # Build LLM registry and inject
    llm_registry = build_llm_registry_from_settings(config.get("llm", {}))
    runtime_ctx["llm_registry"] = llm_registry

    # Build AI Browser and inject (lazy start — not started until first use)
    browser = AIBrowser(
        headless=True,
        screenshot_dir=str(_repo_root() / "data" / "screenshots"),
    )
    runtime_ctx["browser"] = browser

    set_runtime_context(runtime_ctx)

    # Setup static files
    static_dir = _repo_root() / "static"
    setup_static_files(static_dir)

    # Run server
    print("AIOS Web Control Panel starting...")
    print("Open http://localhost:8000 in your browser")
    print("AI Browser API: http://localhost:8000/api/browser/")
    print("LLM Chat API:   http://localhost:8000/api/llm/chat")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
