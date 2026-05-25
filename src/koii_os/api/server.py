from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from ..settings import load_settings, mode_to_initiative, save_settings, update_settings


app = FastAPI(title="AIOS Control Panel")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared runtime context (will be injected from main)
_runtime_context: dict[str, Any] = {}


def set_runtime_context(context: dict[str, Any]) -> None:
    global _runtime_context
    _runtime_context = context


# WebSocket connection manager for real-time events
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# REST API Endpoints
@app.get("/api/agents")
async def get_agents() -> dict[str, Any]:
    scheduler = _runtime_context.get("scheduler")
    if not scheduler:
        return {"agents": []}

    agents = []
    for agent_id, agent in scheduler.agents.items():
        agents.append(
            {
                "agent_id": agent_id,
                "roles": list(agent.roles),
                "attributes": dict(agent.attributes),
            }
        )
    return {"agents": agents}


@app.get("/api/agents/status")
async def get_agents_status() -> dict[str, Any]:
    scheduler = _runtime_context.get("scheduler")
    settings = load_settings()
    builtin = [
        {
            "agent_id": "plugin-development-agent",
            "name": "Plugin Development Agent",
            "type": "plugin",
            "status": "enabled" if settings["agents"].get("plugin_agent_enabled", True) else "disabled",
            "capabilities": ["generate", "test", "debug", "deploy", "version"],
        },
        {
            "agent_id": "core-settings-agent",
            "name": "Core Settings Agent",
            "type": "system",
            "status": "enabled" if settings["agents"].get("core_settings_agent_enabled", True) else "disabled",
            "capabilities": ["kernel", "resources", "zero-trust", "security-policy"],
        },
        {
            "agent_id": "mode-settings-agent",
            "name": "Mode Settings Agent",
            "type": "mode",
            "status": "enabled" if settings["agents"].get("mode_settings_agent_enabled", True) else "disabled",
            "capabilities": ["mode-switch", "initiative-level", "semantic-policy"],
        },
        {
            "agent_id": "browser-agent",
            "name": "Browser Agent",
            "type": "browser",
            "status": "running" if _runtime_context.get("browser") else "not_started",
            "capabilities": ["navigate", "summarize", "screenshot", "web-interaction"],
        },
    ]
    runtime = []
    if scheduler:
        for agent_id, agent in scheduler.agents.items():
            runtime.append(
                {
                    "agent_id": agent_id,
                    "name": agent_id,
                    "type": agent.agent_type,
                    "status": "running",
                    "roles": list(agent.roles),
                    "attributes": dict(agent.attributes),
                }
            )
    return {"agents": builtin + runtime}


@app.post("/api/agents")
async def create_agent(data: dict[str, Any]) -> dict[str, Any]:
    from src.koii_os.agents.types import create_agent

    scheduler = _runtime_context.get("scheduler")
    if not scheduler:
        return {"status": "error", "reason": "scheduler not available"}

    try:
        agent = create_agent(data)
        scheduler.register_agent(agent)
        return {
            "status": "ok",
            "agent_id": agent.agent_id,
            "roles": list(agent.roles),
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.get("/api/settings/llm")
async def get_llm_settings() -> dict[str, Any]:
    llm = dict(load_settings().get("llm", {}))
    llm["api_key_configured"] = bool(llm.get("api_key_secret_id"))
    return {"status": "ok", "llm": llm}


@app.put("/api/settings/llm")
async def put_llm_settings(data: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "provider",
        "base_url",
        "model",
        "api_key_secret_id",
        "temperature",
        "max_tokens",
    }
    values = {key: data[key] for key in allowed if key in data}
    settings = update_settings("llm", values)
    return {"status": "ok", "llm": settings.get("llm", {})}


@app.get("/api/settings/mode")
async def get_mode_settings() -> dict[str, Any]:
    settings = load_settings()
    return {"status": "ok", "mode": settings.get("mode", {}), "agents": settings.get("agents", {})}


@app.put("/api/settings/mode")
async def put_mode_settings(data: dict[str, Any]) -> dict[str, Any]:
    system_mode = str(data.get("system_mode", "") or "")
    mode_values: dict[str, Any] = {}
    if system_mode:
        mode_values["system_mode"] = system_mode
        mode_values["initiative_level"] = mode_to_initiative(system_mode)
    if "initiative_level" in data:
        mode_values["initiative_level"] = data["initiative_level"]
    settings = load_settings()
    if mode_values:
        settings = update_settings("mode", mode_values)
    agent_values = {
        key: bool(data[key])
        for key in ("plugin_agent_enabled", "core_settings_agent_enabled", "mode_settings_agent_enabled")
        if key in data
    }
    if agent_values:
        settings = update_settings("agents", agent_values)
    return {"status": "ok", "mode": settings.get("mode", {}), "agents": settings.get("agents", {})}


@app.post("/api/plugins/generate")
async def generate_plugin(data: dict[str, Any]) -> dict[str, Any]:
    name = _safe_plugin_name(str(data.get("name") or data.get("plugin_name") or "generated-plugin"))
    description = str(data.get("description") or data.get("goal") or "Generated Koii API plugin")
    root = _plugin_root()
    plugin_dir = root / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "version": str(data.get("version") or "0.1.0"),
        "description": description,
        "entrypoint": "plugin.py",
        "status": "generated",
    }
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (plugin_dir / "plugin.py").write_text(_plugin_template(name, description), encoding="utf-8")
    return {"status": "ok", "plugin": manifest, "path": str(plugin_dir)}


@app.post("/api/plugins/test")
async def test_plugin(data: dict[str, Any]) -> dict[str, Any]:
    name = _safe_plugin_name(str(data.get("name") or data.get("plugin_name") or ""))
    if not name:
        return {"status": "error", "reason": "plugin name required"}
    plugin_dir = _plugin_root() / name
    manifest_path = plugin_dir / "plugin.json"
    entrypoint = plugin_dir / "plugin.py"
    checks = {
        "manifest_exists": manifest_path.exists(),
        "entrypoint_exists": entrypoint.exists(),
    }
    if manifest_path.exists():
        try:
            json.loads(manifest_path.read_text(encoding="utf-8"))
            checks["manifest_valid"] = True
        except json.JSONDecodeError:
            checks["manifest_valid"] = False
    ok = all(checks.values())
    return {"status": "ok" if ok else "error", "plugin": name, "checks": checks}


@app.post("/api/plugins/deploy")
async def deploy_plugin(data: dict[str, Any]) -> dict[str, Any]:
    name = _safe_plugin_name(str(data.get("name") or data.get("plugin_name") or ""))
    if not name:
        return {"status": "error", "reason": "plugin name required"}
    plugin_dir = _plugin_root() / name
    manifest_path = plugin_dir / "plugin.json"
    if not manifest_path.exists():
        return {"status": "error", "reason": "plugin manifest not found"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "deployed"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    await publish_event({"type": "plugin_deployed", "plugin": name})
    return {"status": "ok", "plugin": manifest, "path": str(plugin_dir)}


@app.get("/api/tasks")
async def get_tasks() -> dict[str, Any]:
    task_center = _runtime_context.get("task_center")
    if not task_center:
        return {"tasks": []}

    tasks = []
    store = _runtime_context.get("store")
    if store:
        events = store.recent(limit=100)
        for evt in events:
            topic = evt.get("topic", "")
            if topic in ("task_center.attempt.started", "task_center.attempt.completed"):
                tasks.append({
                    "event_id": evt.get("id"),
                    "event_type": topic,
                    "timestamp": evt.get("ts"),
                    "data": evt.get("payload")
                })
    return {"tasks": tasks}


@app.post("/api/tasks")
async def create_task(data: dict[str, Any]) -> dict[str, Any]:
    task_center = _runtime_context.get("task_center")
    if not task_center:
        return {"status": "error", "reason": "task_center not available"}

    try:
        result = await task_center.run_goal_tasks(data)
        return {
            "status": "ok",
            "results": result,
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.get("/api/resources")
async def get_resources() -> dict[str, Any]:
    try:
        resource_manager = _runtime_context.get("resource_manager")
        if not resource_manager:
            return {"status": "ok", "nodes": []}

        overview = resource_manager.overview()
        return overview
    except Exception as e:
        return {"status": "error", "reason": str(e), "nodes": []}


# WebSocket for real-time event streaming
@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"type": "client_message", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Event publisher for internal use
async def publish_event(event: dict[str, Any]) -> None:
    await manager.broadcast({"type": "event", "data": event})


# ── LLM API ──────────────────────────────────────────────────────────────────

@app.get("/api/llm/models")
async def get_llm_models() -> dict[str, Any]:
    llm_registry = _runtime_context.get("llm_registry")
    if not llm_registry:
        return {"models": [], "providers": []}
    models = list(llm_registry.model_to_provider.keys())
    providers = list(llm_registry.providers.keys())
    return {"models": models, "providers": providers}


@app.post("/api/llm/chat")
async def llm_chat(data: dict[str, Any]) -> dict[str, Any]:
    llm_registry = _runtime_context.get("llm_registry")
    if not llm_registry:
        return {"status": "error", "reason": "llm_registry not available"}
    model = str(data.get("model", "mock-llm-v1"))
    prompt = str(data.get("prompt", ""))
    if not prompt:
        return {"status": "error", "reason": "prompt required"}
    try:
        result = await llm_registry.infer(model_name=model, prompt=prompt)
        await publish_event({"type": "llm_chat", "model": model, "prompt": prompt[:100], "output": str(result.get("output", ""))[:200]})
        return result
    except Exception as e:
        return {"status": "error", "reason": str(e)}


# ── AI Browser API ────────────────────────────────────────────────────────────

@app.get("/api/browser/status")
async def browser_status() -> dict[str, Any]:
    browser = _runtime_context.get("browser")
    if not browser:
        return {"status": "not_started", "url": ""}
    started = browser._page is not None
    return {
        "status": "running" if started else "idle",
        "url": browser.current_url if started else "",
    }


@app.post("/api/browser/start")
async def browser_start(data: dict[str, Any] | None = None) -> dict[str, Any]:
    browser = _runtime_context.get("browser")
    if not browser:
        return {"status": "error", "reason": "browser not in runtime context"}
    headless = bool((data or {}).get("headless", True))
    browser.headless = headless
    try:
        if browser._page is None:
            await browser.start()
        return {"status": "ok", "headless": headless}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.post("/api/browser/stop")
async def browser_stop() -> dict[str, Any]:
    browser = _runtime_context.get("browser")
    if not browser:
        return {"status": "error", "reason": "browser not in runtime context"}
    try:
        await browser.stop()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.post("/api/browser/action")
async def browser_action(action: dict[str, Any]) -> dict[str, Any]:
    """Execute a single browser action."""
    browser = _runtime_context.get("browser")
    if not browser:
        return {"status": "error", "reason": "browser not available"}
    if browser._page is None:
        await browser.start()
    try:
        result = await browser.run_action(action)
        await publish_event({"type": "browser_action", "action": action.get("action"), "result": result.get("status")})
        return result
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.post("/api/browser/goal")
async def browser_goal(data: dict[str, Any]) -> dict[str, Any]:
    """Run an autonomous LLM-driven browser goal."""
    browser = _runtime_context.get("browser")
    llm_registry = _runtime_context.get("llm_registry")
    if not browser or not llm_registry:
        return {"status": "error", "reason": "browser or llm_registry not available"}
    from src.koii_os.browser.agent import BrowserAgent
    if browser._page is None:
        await browser.start()
    goal = str(data.get("goal", ""))
    model = str(data.get("model", "gpt-4o-mini"))
    max_steps = int(data.get("max_steps", 10))
    if not goal:
        return {"status": "error", "reason": "goal required"}
    try:
        agent = BrowserAgent(browser=browser, llm_registry=llm_registry)
        result = await agent.run_goal(goal=goal, model=model, max_steps=max_steps)
        await publish_event({"type": "browser_goal", "goal": goal, "steps": result.get("steps"), "summary": result.get("summary", "")[:200]})
        return result
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.get("/api/browser/screenshot")
async def browser_screenshot() -> Any:
    """Return current page screenshot as base64."""
    browser = _runtime_context.get("browser")
    if not browser or browser._page is None:
        return {"status": "error", "reason": "browser not running"}
    result = await browser.screenshot("live")
    return result


# Serve static files (HTML/JS/CSS)
@app.get("/")
async def root() -> FileResponse:
    """Serve the main index.html page."""
    static_dir = Path(_runtime_context.get("static_dir", "static"))
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return FileResponse("static/index.html")


def setup_static_files(static_dir: Path) -> None:
    """Mount static files directory."""
    if static_dir.exists():
        _runtime_context["static_dir"] = str(static_dir)
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def _plugin_root() -> Path:
    root = Path(_runtime_context.get("plugin_root") or "/opt/aios/plugins")
    if not root.parent.exists() or not root.parent.is_dir():
        root = Path.cwd() / "data" / "plugins"
    return root


def _safe_plugin_name(name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_.-]+", "-", name.strip().lower()).strip(".-")
    return normalized[:80]


def _plugin_template(name: str, description: str) -> str:
    return f'''"""Koii generated API plugin: {name}."""

DESCRIPTION = {description!r}


def run(payload):
    return {{
        "status": "ok",
        "plugin": {name!r},
        "description": DESCRIPTION,
        "payload": payload,
    }}
'''
