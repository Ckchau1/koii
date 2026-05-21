from __future__ import annotations

import asyncio
import os
from pathlib import Path

from .koii_os.automation.daemon import TaskCenterDaemon
from .koii_os.automation.planner import AutonomousTaskLoop, TaskPlanner
from .koii_os.automation.runner import TaskAutomationEngine
from .koii_os.automation.task_center import TaskCenter
from .koii_os.agents.types import create_agent
from .koii_os.browser import AIBrowser, MinBrowserController
from .koii_os.config.loader import load_config
from .koii_os.control_plane.resource_federation import GlobalResourceManager
from .koii_os.control_plane.workflow_runtime import WorkflowRuntime
from .koii_os.core.kernel import KernelRuntime
from .koii_os.core.scheduler import AgentScheduler
from .koii_os.llm.registry import build_llm_registry_from_settings, resolve_selected_model
from .koii_os.mesh.collab import CollaborationEngine
from .koii_os.mesh.registry import AgentRegistry
from .koii_os.security.policy import SecurityPolicyEngine
from .koii_os.state.store import build_event_store
from .koii_os.tools.os_control import OSToolExecutor
from .koii_os.transport.bus import build_message_bus


async def bootstrap(config_path: str) -> None:
    cfg = load_config(config_path)

    kernel_cfg = cfg.get("kernel", {})
    max_agents = int(kernel_cfg.get("max_agents", 10000))
    tick_ms = int(kernel_cfg.get("tick_ms", 1))

    store = build_event_store(cfg.get("persistence", {}))
    scheduler = AgentScheduler(max_agents=max_agents, state_store=store)
    registry = AgentRegistry()
    bus = build_message_bus(cfg.get("transport", {}))

    bus.subscribe("task.delegated", lambda event: store.append("mesh.task.delegated", event))

    agent_roles: dict[str, list[str]] = {}
    agent_attrs: dict[str, dict[str, object]] = {}

    for acfg in cfg.get("agents", []):
        agent = create_agent(acfg)
        scheduler.register_agent(agent)
        registry.register(agent)
        agent_roles[agent.agent_id] = list(agent.roles)
        agent_attrs[agent.agent_id] = dict(agent.attributes)

    security = SecurityPolicyEngine(
        agent_roles=agent_roles,
        agent_attrs=agent_attrs,
        zero_trust=bool(cfg.get("security", {}).get("zero_trust", True)),
    )
    llm_registry = build_llm_registry_from_settings(cfg.get("llm", {}))

    kernel = KernelRuntime(
        scheduler=scheduler,
        security=security,
        llm_registry=llm_registry,
        tick_ms=tick_ms,
    )

    selected_profile = os.getenv("KOII_LLM_PROFILE")
    selected_capability = os.getenv("KOII_LLM_CAPABILITY")
    selected_model_override = os.getenv("KOII_LLM_MODEL")
    selected_model = resolve_selected_model(
        cfg=cfg.get("llm", {}),
        profile_name=selected_profile,
        capability_name=selected_capability,
        explicit_model=selected_model_override,
    )

    collab = CollaborationEngine(scheduler=scheduler, registry=registry, bus=bus)
    tool_executor = OSToolExecutor(
        allowed_shell_commands=list(cfg.get("automation", {}).get("allowed_shell_commands", []))
    )

    # Initialize browser for autonomous agents
    browser_backend = os.getenv('KOII_BROWSER_BACKEND', 'playwright').lower()
    browser_headless = os.getenv('KOII_BROWSER_HEADLESS', 'true').lower() == 'true'
    browser_screenshot_dir = os.getenv('KOII_BROWSER_SCREENSHOT_DIR', './data/screenshots')
    if browser_backend == 'minbrowser':
        min_launch_cmd = os.getenv('KOII_BROWSER_LAUNCH_CMD')
        launch_cmd = min_launch_cmd.split() if min_launch_cmd else None
        ai_browser = MinBrowserController(
            base_url=os.getenv('KOII_BROWSER_MIN_URL', 'http://127.0.0.1:43210'),
            auth_token=os.getenv('KOII_BROWSER_AGENT_TOKEN', 'koii-default-token'),
            launch_cmd=launch_cmd,
            screenshot_dir=browser_screenshot_dir,
            headless=browser_headless,
        )
    else:
        ai_browser = AIBrowser(headless=browser_headless, screenshot_dir=browser_screenshot_dir)

    automation = TaskAutomationEngine(
        kernel=kernel,
        security=security,
        tool_executor=tool_executor,
        state_store=store,
        browser=ai_browser,
    )
    autonomy_cfg = cfg.get("autonomy", {})
    planner = TaskPlanner(
        kernel=kernel,
        planner_model=str(autonomy_cfg.get("planner_model") or selected_model),
        state_store=store,
        browser=ai_browser,
    )
    autonomous_loop = AutonomousTaskLoop(planner=planner, runner=automation, state_store=store)
    task_center = TaskCenter(autonomous_loop=autonomous_loop, state_store=store)
    daemon = TaskCenterDaemon(task_center=task_center, state_store=store)
    resource_manager = GlobalResourceManager(state_store=store)
    resource_manager.load_nodes(cfg.get("infrastructure", {}))
    workflow_runtime = WorkflowRuntime(
        task_center=task_center,
        resource_manager=resource_manager,
        state_store=store,
    )

    objective = "plan GTM strategy for a new AI product"
    tasks = collab.decompose(objective)

    pending = store.recover_pending_tasks()
    if pending:
        for evt in pending:
            await scheduler.submit(agent_id=evt["agent_id"], task=evt["task"])

    try:
        # Start browser before automation tasks
        await ai_browser.start()

        await collab.delegate(tasks)
        scheduled_results = await kernel.run_for(duration_s=0.05)

        parallel_results = await collab.execute_parallel(tasks)
        synthesis = collab.synthesize(parallel_results)

        model_call = await kernel.syscall_model_infer(
            agent_id="task-1",
            model_name=selected_model,
            prompt="Draft 3 strategic priorities for Q3.",
        )
        automation_results = await automation.run_startup_tasks(cfg.get("automation", {}))
        autonomous_results = await task_center.run_goal_tasks(autonomy_cfg)
        daemon_results = await daemon.run(cfg.get("daemon", {}))
        workflow_results = await workflow_runtime.run_workflows(cfg.get("collaboration", {}), autonomy_cfg)

        print("=== Scheduled Results ===")
        for row in scheduled_results:
            print(row)

        print("\n=== Parallel Synthesis ===")
        print(synthesis)

        print("\n=== Model Syscall ===")
        print(model_call)

        print("\n=== Automation Results ===")
        print(automation_results)

        print("\n=== Autonomous Goal Results ===")
        print(autonomous_results)

        print("\n=== Daemon Cycle Results ===")
        print(daemon_results)

        print("\n=== Global Resource Overview ===")
        print(resource_manager.overview())

        print("\n=== Workflow Runtime Results ===")
        print(workflow_results)

        print("\n=== Event Store (Recent) ===")
        print(store.recent(limit=5))
    finally:
        # Stop browser after all tasks complete
        await ai_browser.stop()


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    cfg_path = root / "agent-config.yaml"
    asyncio.run(bootstrap(str(cfg_path)))


if __name__ == "__main__":
    main()
