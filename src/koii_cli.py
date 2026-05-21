from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import yaml

from src.koii_os.automation.planner import AutonomousTaskLoop, TaskPlanner
from src.koii_os.automation.runner import TaskAutomationEngine
from src.koii_os.automation.task_center import TaskCenter
from src.koii_os.agents.types import create_agent
from src.koii_os.config.loader import load_config
from src.koii_os.control_plane.resource_federation import GlobalResourceManager
from src.koii_os.core.kernel import KernelRuntime
from src.koii_os.core.scheduler import AgentScheduler
from src.koii_os.llm.registry import build_llm_registry, resolve_selected_model
from src.koii_os.security.policy import SecurityPolicyEngine
from src.koii_os.state.store import build_event_store
from src.koii_os.tools.messaging import CodingWorkspaceIntegration, TelegramNotifier, WhatsAppNotifier
from src.koii_os.tools.os_control import OSToolExecutor


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _config_path() -> Path:
    return _repo_root() / "agent-config.yaml"


def _agent_registry_path() -> Path:
    path = _repo_root() / "data" / "agent-registry.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_registry() -> dict[str, Any]:
    path = _agent_registry_path()
    if not path.exists():
        return {"agents": []}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        return {"agents": []}
    data.setdefault("agents", [])
    return data


def _save_registry(data: dict[str, Any]) -> None:
    path = _agent_registry_path()
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)


def _build_runtime(cfg: dict[str, Any]) -> dict[str, Any]:
    kernel_cfg = cfg.get("kernel", {})
    max_agents = int(kernel_cfg.get("max_agents", 10000))
    tick_ms = int(kernel_cfg.get("tick_ms", 1))

    store = build_event_store(cfg.get("persistence", {}))
    scheduler = AgentScheduler(max_agents=max_agents, state_store=store)

    agent_roles: dict[str, list[str]] = {}
    agent_attrs: dict[str, dict[str, object]] = {}

    for acfg in cfg.get("agents", []):
        agent = create_agent(acfg)
        scheduler.register_agent(agent)
        agent_roles[agent.agent_id] = list(agent.roles)
        agent_attrs[agent.agent_id] = dict(agent.attributes)

    security = SecurityPolicyEngine(
        agent_roles=agent_roles,
        agent_attrs=agent_attrs,
        zero_trust=bool(cfg.get("security", {}).get("zero_trust", True)),
    )

    llm_registry = build_llm_registry(cfg.get("llm", {}))
    kernel = KernelRuntime(
        scheduler=scheduler,
        security=security,
        llm_registry=llm_registry,
        tick_ms=tick_ms,
    )

    selected_model = resolve_selected_model(
        cfg=cfg.get("llm", {}),
        profile_name=None,
        capability_name=None,
        explicit_model=None,
    )

    tool_executor = OSToolExecutor(
        allowed_shell_commands=list(cfg.get("automation", {}).get("allowed_shell_commands", []))
    )
    automation = TaskAutomationEngine(
        kernel=kernel,
        security=security,
        tool_executor=tool_executor,
        state_store=store,
    )
    autonomy_cfg = cfg.get("autonomy", {})
    planner = TaskPlanner(
        kernel=kernel,
        planner_model=str(autonomy_cfg.get("planner_model") or selected_model),
        state_store=store,
    )
    loop = AutonomousTaskLoop(planner=planner, runner=automation, state_store=store)
    task_center = TaskCenter(autonomous_loop=loop, state_store=store)

    resource_manager = GlobalResourceManager(state_store=store)
    resource_manager.load_nodes(cfg.get("infrastructure", {}))

    return {
        "task_center": task_center,
        "resource_manager": resource_manager,
        "autonomy_cfg": autonomy_cfg,
        "scheduler": scheduler,
        "store": store,
    }


def cmd_resource_list(_: argparse.Namespace) -> None:
    cfg = load_config(_config_path())
    runtime = _build_runtime(cfg)
    print(json.dumps(runtime["resource_manager"].overview(), ensure_ascii=False, indent=2))


def cmd_resource_reserve(args: argparse.Namespace) -> None:
    cfg = load_config(_config_path())
    runtime = _build_runtime(cfg)
    result = runtime["resource_manager"].reserve(
        cpu=args.cpu,
        memory_mb=args.memory_mb,
        gpu=args.gpu,
        preferred_region=args.region,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_resource_release(args: argparse.Namespace) -> None:
    cfg = load_config(_config_path())
    runtime = _build_runtime(cfg)
    result = runtime["resource_manager"].release(
        node_id=args.node,
        cpu=args.cpu,
        memory_mb=args.memory_mb,
        gpu=args.gpu,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_agent_create(args: argparse.Namespace) -> None:
    data = _load_registry()
    agents = data.get("agents", [])

    if any(a.get("name") == args.name for a in agents):
        print(json.dumps({"status": "error", "reason": f"agent exists: {args.name}"}, ensure_ascii=False, indent=2))
        return

    entry = {
        "name": args.name,
        "type": args.type,
        "goal": args.goal,
    }
    agents.append(entry)
    data["agents"] = agents
    _save_registry(data)
    print(json.dumps({"status": "ok", "agent": entry, "registry": str(_agent_registry_path())}, ensure_ascii=False, indent=2))


def cmd_agent_list(_: argparse.Namespace) -> None:
    data = _load_registry()
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def _run_agent_async(name: str, watch: bool) -> dict[str, Any]:
    data = _load_registry()
    entry = next((a for a in data.get("agents", []) if a.get("name") == name), None)
    if entry is None:
        return {"status": "error", "reason": f"unknown agent: {name}"}

    cfg = load_config(_config_path())
    runtime = _build_runtime(cfg)
    autonomy_cfg = dict(runtime["autonomy_cfg"])
    autonomy_cfg["enabled"] = True
    autonomy_cfg["goal_tasks"] = [
        {
            "id": f"cli-{name}",
            "goal": str(entry.get("goal", "")),
            "cwd": ".",
            "retry_limit": 1,
        }
    ]

    results = await runtime["task_center"].run_goal_tasks(autonomy_cfg)
    payload = {"status": "ok", "agent": name, "results": results}
    if watch:
        payload["watch"] = {
            "mode": "single-run",
            "note": "watch mode in prototype prints one execution cycle",
        }
    return payload


def cmd_agent_run(args: argparse.Namespace) -> None:
    result = asyncio.run(_run_agent_async(name=args.name, watch=args.watch))
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_notify_telegram(args: argparse.Namespace) -> None:
    cfg = load_config(_config_path())
    messaging_cfg = cfg.get("messaging", {})
    bot_token = args.bot_token or messaging_cfg.get("telegram", {}).get("bot_token")
    chat_id = args.chat_id or messaging_cfg.get("telegram", {}).get("chat_id")
    notifier = TelegramNotifier(bot_token=bot_token or "", chat_id=chat_id or "")
    result = notifier.send_message(args.message)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_notify_whatsapp(args: argparse.Namespace) -> None:
    cfg = load_config(_config_path())
    messaging_cfg = cfg.get("messaging", {})
    access_token = args.access_token or messaging_cfg.get("whatsapp", {}).get("access_token")
    phone_id = args.phone_number_id or messaging_cfg.get("whatsapp", {}).get("phone_number_id")
    recipient = args.recipient or messaging_cfg.get("whatsapp", {}).get("recipient")
    notifier = WhatsAppNotifier(access_token=access_token or "", phone_number_id=phone_id or "", recipient=recipient or "")
    result = notifier.send_message(args.message)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_workspace_status(args: argparse.Namespace) -> None:
    cfg = load_config(_config_path())
    workspace_cfg = cfg.get("workspace", {})
    workspace_path = args.path or workspace_cfg.get("path") or "."
    workspace = CodingWorkspaceIntegration(workspace_path=workspace_path)
    result = workspace.workspace_status()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="koii", description="Koii-style prototype CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    resource = sub.add_parser("resource", help="resource operations")
    resource_sub = resource.add_subparsers(dest="resource_cmd", required=True)

    r_list = resource_sub.add_parser("list", help="show resource overview")
    r_list.set_defaults(func=cmd_resource_list)

    r_reserve = resource_sub.add_parser("reserve", help="reserve resources")
    r_reserve.add_argument("--cpu", type=int, default=1)
    r_reserve.add_argument("--memory-mb", type=int, default=1024)
    r_reserve.add_argument("--gpu", type=int, default=0)
    r_reserve.add_argument("--region", type=str, default=None)
    r_reserve.set_defaults(func=cmd_resource_reserve)

    r_release = resource_sub.add_parser("release", help="release resources")
    r_release.add_argument("--node", type=str, required=True)
    r_release.add_argument("--cpu", type=int, default=1)
    r_release.add_argument("--memory-mb", type=int, default=1024)
    r_release.add_argument("--gpu", type=int, default=0)
    r_release.set_defaults(func=cmd_resource_release)

    agent = sub.add_parser("agent", help="agent operations")
    agent_sub = agent.add_subparsers(dest="agent_cmd", required=True)

    a_create = agent_sub.add_parser("create", help="create an agent entry")
    a_create.add_argument("--name", type=str, required=True)
    a_create.add_argument("--type", type=str, default="task")
    a_create.add_argument("--goal", type=str, required=True)
    a_create.set_defaults(func=cmd_agent_create)

    a_list = agent_sub.add_parser("list", help="list registered agents")
    a_list.set_defaults(func=cmd_agent_list)

    a_run = agent_sub.add_parser("run", help="run a registered agent")
    a_run.add_argument("name", type=str)
    a_run.add_argument("--watch", action="store_true")
    a_run.set_defaults(func=cmd_agent_run)

    notify = sub.add_parser("notify", help="send notifications via messaging channels")
    notify_sub = notify.add_subparsers(dest="notify_cmd", required=True)

    tgram = notify_sub.add_parser("telegram", help="send a Telegram message")
    tgram.add_argument("--message", type=str, required=True)
    tgram.add_argument("--bot-token", type=str, default=None)
    tgram.add_argument("--chat-id", type=str, default=None)
    tgram.set_defaults(func=cmd_notify_telegram)

    whatsapp = notify_sub.add_parser("whatsapp", help="send a WhatsApp message")
    whatsapp.add_argument("--message", type=str, required=True)
    whatsapp.add_argument("--access-token", type=str, default=None)
    whatsapp.add_argument("--phone-number-id", type=str, default=None)
    whatsapp.add_argument("--recipient", type=str, default=None)
    whatsapp.set_defaults(func=cmd_notify_whatsapp)

    workspace = sub.add_parser("workspace", help="inspect coding workspace status")
    workspace.add_argument("--path", type=str, default=None)
    workspace.set_defaults(func=cmd_workspace_status)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
