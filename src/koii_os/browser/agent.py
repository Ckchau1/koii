from __future__ import annotations

import json
from typing import Any

from .engine import AIBrowser


class BrowserAgent:
    """
    LLM-driven autonomous browser agent.
    Given a goal (e.g. "search for X and summarise results"),
    it uses an LLM to plan and execute a sequence of browser actions.
    """

    def __init__(self, browser: AIBrowser, llm_registry: Any) -> None:
        self.browser = browser
        self.llm_registry = llm_registry

    async def _plan_next_action(
        self,
        goal: str,
        history: list[dict[str, Any]],
        page_text: str,
        page_url: str,
        elements: list[dict[str, Any]],
        model: str,
    ) -> dict[str, Any]:
        """Ask LLM what to do next given the current page state."""
        history_summary = "\n".join(
            f"  step {i+1}: {h['action']} -> {h['result'].get('status','?')}"
            for i, h in enumerate(history[-5:])
        )
        elements_str = json.dumps(elements[:15], ensure_ascii=False)
        prompt = f"""You are an AI controlling a web browser to achieve a goal.

Goal: {goal}

Current URL: {page_url}
Page text (first 1500 chars): {page_text[:1500]}
Interactive elements: {elements_str}

Recent actions:
{history_summary or "  (none yet)"}

Decide the NEXT single action. Respond with ONLY a JSON object like one of these:
  {{"action": "navigate", "url": "https://example.com"}}
  {{"action": "click", "text": "Search"}}
  {{"action": "click", "selector": "#submit"}}
  {{"action": "type", "selector": "input[name=q]", "text": "query here"}}
  {{"action": "press", "key": "Enter"}}
  {{"action": "get_text"}}
  {{"action": "get_links"}}
  {{"action": "screenshot", "label": "result"}}
  {{"action": "done", "summary": "what was accomplished"}}

Rules:
- If the goal is accomplished, return {{"action": "done", "summary": "..."}}.
- Never repeat the same failed action twice.
- Prefer get_text before clicking to understand the page.
- Only return the JSON, nothing else.
"""
        result = await self.llm_registry.infer(model_name=model, prompt=prompt)
        raw = result.get("output", "{}")
        try:
            # Strip markdown code fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                lines = clean.split("\n")
                clean = "\n".join(lines[1:-1]) if len(lines) > 2 else clean
            action = json.loads(clean)
        except Exception:
            # Fallback: try to extract JSON from the string
            import re
            match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
            if match:
                try:
                    action = json.loads(match.group(0))
                except Exception:
                    action = {"action": "done", "summary": f"LLM parse failed: {raw[:200]}"}
            else:
                action = {"action": "done", "summary": f"LLM returned non-JSON: {raw[:200]}"}
        return action

    async def run_goal(
        self,
        goal: str,
        model: str = "gpt-4o-mini",
        max_steps: int = 12,
    ) -> dict[str, Any]:
        """Autonomously browse to achieve the given goal."""
        if not self.browser._page:
            await self.browser.start()

        history: list[dict[str, Any]] = []
        final_summary = ""

        for step in range(max_steps):
            # Gather current page state
            text_res = await self.browser.get_text()
            elem_res = await self.browser.find_elements(goal)
            page_text = text_res.get("text", "")
            page_url = self.browser.current_url
            elements = elem_res.get("elements", [])

            # Ask LLM for next action
            action = await self._plan_next_action(
                goal=goal,
                history=history,
                page_text=page_text,
                page_url=page_url,
                elements=elements,
                model=model,
            )

            if action.get("action") == "done":
                final_summary = str(action.get("summary", "Goal completed."))
                break

            # Execute the action
            result = await self.browser.run_action(action)
            history.append({"step": step + 1, "action": action, "result": result})

            if result.get("status") == "error":
                # On persistent error, let LLM decide differently next time
                pass

        return {
            "status": "ok",
            "goal": goal,
            "steps": len(history),
            "history": history,
            "summary": final_summary or "Max steps reached.",
            "final_url": self.browser.current_url,
        }
