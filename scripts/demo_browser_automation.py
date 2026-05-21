#!/usr/bin/env python3
"""
Demo: Browser Automation with AIOS Autonomous Planner

This script demonstrates how the AIOS autonomous planner can use the AI Browser
to perform web automation tasks. The planner generates steps that include browser
actions (navigate, click, screenshot, etc.) which are executed by the TaskAutomationEngine.

Example Goals:
  - "Take a screenshot of GitHub homepage"
  - "Search for Python docs on Google"
  - "Navigate to example.com and extract all links"
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.koii_os.browser.engine import AIBrowser
from src.koii_os.automation.runner import TaskAutomationEngine
from src.koii_os.automation.planner import TaskPlanner
from src.koii_os.core.kernel import KernelRuntime
from src.koii_os.core.scheduler import AgentScheduler
from src.koii_os.llm.registry import build_llm_registry
from src.koii_os.security.policy import SecurityPolicyEngine
from src.koii_os.state.store import EventStore
from src.koii_os.tools.os_control import OSToolExecutor


async def demo_browser_navigation() -> None:
    """Demo 1: Simple browser navigation and screenshot"""
    print("\n=== DEMO 1: Browser Navigation ===")

    browser = AIBrowser(headless=True, screenshot_dir="./data/screenshots")
    await browser.start()

    try:
        # Navigate to a website
        nav_result = await browser.navigate("https://example.com")
        print(f"Navigation result: {nav_result}")

        # Take a screenshot
        screenshot_result = await browser.screenshot(label="example-com")
        if screenshot_result.get("status") == "ok":
            print(f"Screenshot saved to: {screenshot_result.get('path')}")
        else:
            print(f"Screenshot failed: {screenshot_result}")

        # Get page text
        text_result = await browser.get_text()
        if text_result.get("status") == "ok":
            text = text_result.get("text", "")[:200]
            print(f"Page text (first 200 chars): {text}")
        else:
            print(f"Get text failed: {text_result}")

        # Get all links on the page
        links_result = await browser.get_links()
        if links_result.get("status") == "ok":
            links = links_result.get("links", [])
            print(f"Found {len(links)} links on page")
            for link in links[:3]:
                print(f"  - {link.get('text', 'N/A')}: {link.get('href', 'N/A')}")

    finally:
        await browser.stop()


async def demo_task_automation_with_browser() -> None:
    """Demo 2: Using TaskAutomationEngine with browser steps"""
    print("\n=== DEMO 2: Task Automation with Browser Steps ===")

    browser = AIBrowser(headless=True, screenshot_dir="./data/screenshots")
    await browser.start()

    try:
        # Setup minimal components
        scheduler = AgentScheduler(max_agents=10)
        llm_registry = build_llm_registry({"providers": [{"name": "mock", "type": "mock"}]})
        security = SecurityPolicyEngine(agent_roles={"agent-1": ["worker"]}, agent_attrs={}, zero_trust=False)

        kernel = KernelRuntime(scheduler=scheduler, security=security, llm_registry=llm_registry, tick_ms=1)
        tool_executor = OSToolExecutor(allowed_shell_commands=["echo", "pwd"])

        automation = TaskAutomationEngine(
            kernel=kernel,
            security=security,
            tool_executor=tool_executor,
            state_store=None,
            browser=browser,
        )

        # Define a task with browser steps
        task = {
            "id": "browser-task-1",
            "description": "Navigate and screenshot example.com",
            "steps": [
                {
                    "type": "browser",
                    "action": {"action": "navigate", "url": "https://example.com"},
                },
                {
                    "type": "browser",
                    "action": {"action": "screenshot", "label": "example-page"},
                },
                {
                    "type": "browser",
                    "action": {"action": "get_text"},
                },
            ],
        }

        # Run the task
        result = await automation.run_task(agent_id="agent-1", task=task)
        print(f"Task result: {result.get('status')}")
        print(f"Outputs:")
        for output in result.get("outputs", []):
            step_type = output.get("type")
            step_result = output.get("result", {})
            status = step_result.get("status")
            print(f"  Step {output.get('step')} ({step_type}): {status}")
            if status == "ok":
                if step_type == "browser":
                    if "path" in step_result:
                        print(f"    Screenshot: {step_result.get('path')}")

    finally:
        await browser.stop()


async def demo_planner_with_browser() -> None:
    """Demo 3: Using TaskPlanner with browser-capable prompts"""
    print("\n=== DEMO 3: Task Planner with Browser Support ===")

    # Setup minimal components
    scheduler = AgentScheduler(max_agents=10)
    llm_registry = build_llm_registry({"providers": [{"name": "mock", "type": "mock"}]})
    security = SecurityPolicyEngine(agent_roles={"agent-1": ["worker"]}, agent_attrs={}, zero_trust=False)

    kernel = KernelRuntime(scheduler=scheduler, security=security, llm_registry=llm_registry, tick_ms=1)

    browser = AIBrowser(headless=True, screenshot_dir="./data/screenshots")

    planner = TaskPlanner(
        kernel=kernel,
        planner_model="mock-llm-v1",
        state_store=None,
        browser=browser,
    )

    # The planner now supports browser steps in its prompts
    goal = "Take a screenshot of example.com"
    observations: list[dict] = []

    plan = await planner.plan(agent_id="agent-1", goal=goal, observations=observations, cwd=".")

    print(f"Generated plan for goal: '{goal}'")
    print(f"Plan steps:")
    for i, step in enumerate(plan.get("steps", []), 1):
        step_type = step.get("type")
        print(f"  {i}. Type: {step_type}")
        if step_type == "shell":
            print(f"     Command: {step.get('command')}")
        elif step_type == "browser":
            action = step.get("action", {})
            print(f"     Action: {action.get('action')} {action.get('url', action.get('selector', ''))}")
        elif step_type == "model":
            print(f"     Model: {step.get('model')}")


async def main() -> None:
    """Run all demos"""
    print("AIOS Browser Automation Demo")
    print("=" * 50)

    try:
        await demo_browser_navigation()
        await demo_task_automation_with_browser()
        await demo_planner_with_browser()

        print("\n" + "=" * 50)
        print("✓ All demos completed successfully!")
        print("\nNext steps:")
        print("  1. Run the full AIOS system: python -m src.main")
        print("  2. Check screenshots in ./data/screenshots")
        print("  3. Monitor event store for autonomy events")

    except Exception as e:
        print(f"\n✗ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
