from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure imports work when running as a script.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.koii_os.transport.bus import NatsBus


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex((host, port)) == 0


def _find_nats_server_bin() -> Path | None:
    candidates = [
        REPO_ROOT / "tools" / "nats-server-v2.10.18-windows-amd64" / "nats-server.exe",
        REPO_ROOT / "tools" / "nats-server-v2.10.18-linux-amd64" / "nats-server",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _start_local_nats_if_needed(nats_url: str) -> tuple[subprocess.Popen[str] | None, bool]:
    # Supports URL forms like nats://127.0.0.1:4222.
    host_port = nats_url.replace("nats://", "")
    host, port_str = host_port.split(":", 1)
    port = int(port_str)

    if _port_open(host, port):
        return None, False

    nats_bin = _find_nats_server_bin()
    if nats_bin is None:
        return None, False

    proc = subprocess.Popen(
        [str(nats_bin), "-p", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return proc, True


async def _worker(node_id: str, run_id: str, nats_url: str) -> int:
    bus = NatsBus(nats_url=nats_url)
    stop_event = asyncio.Event()

    async def _publish_ack(payload: dict[str, Any]) -> None:
        await bus.publish(
            "mesh.integration.ack",
            {
                "run_id": run_id,
                "node_id": node_id,
                "received": payload,
            },
        )

    def _on_ping(message: dict[str, Any]) -> None:
        if message.get("run_id") != run_id:
            return
        asyncio.create_task(_publish_ack(message))

    def _on_stop(message: dict[str, Any]) -> None:
        if message.get("run_id") != run_id:
            return
        stop_event.set()

    bus.subscribe("mesh.integration.ping", _on_ping)
    bus.subscribe("mesh.integration.stop", _on_stop)

    try:
        await asyncio.wait_for(stop_event.wait(), timeout=60)
    except TimeoutError:
        return 1

    return 0


async def _coordinator(nats_url: str, timeout_s: float, start_server: bool) -> int:
    run_id = f"run-{os.getpid()}"

    nats_proc: subprocess.Popen[str] | None = None
    started_here = False
    if start_server:
        nats_proc, started_here = _start_local_nats_if_needed(nats_url)
        await asyncio.sleep(0.8)

    workers: list[subprocess.Popen[str]] = []
    try:
        cmd_base = [sys.executable, str(Path(__file__).resolve()), "worker", "--run-id", run_id, "--nats-url", nats_url]
        workers.append(subprocess.Popen(cmd_base + ["--node-id", "node-a"], cwd=str(REPO_ROOT)))
        workers.append(subprocess.Popen(cmd_base + ["--node-id", "node-b"], cwd=str(REPO_ROOT)))

        bus = NatsBus(nats_url=nats_url)
        seen: set[str] = set()
        done = asyncio.Event()

        def _on_ack(message: dict[str, Any]) -> None:
            if message.get("run_id") != run_id:
                return
            node_id = str(message.get("node_id", ""))
            if node_id:
                seen.add(node_id)
            if {"node-a", "node-b"}.issubset(seen):
                done.set()

        bus.subscribe("mesh.integration.ack", _on_ack)
        await asyncio.sleep(0.5)

        await bus.publish(
            "mesh.integration.ping",
            {
                "run_id": run_id,
                "payload": "hello-mesh",
            },
        )

        try:
            await asyncio.wait_for(done.wait(), timeout=timeout_s)
        except TimeoutError:
            result = {
                "status": "error",
                "reason": "timeout waiting for acks",
                "seen": sorted(seen),
                "expected": ["node-a", "node-b"],
                "run_id": run_id,
            }
            print(json.dumps(result, ensure_ascii=False))
            return 1

        await bus.publish("mesh.integration.stop", {"run_id": run_id})
        await asyncio.sleep(0.5)

        result = {
            "status": "ok",
            "run_id": run_id,
            "seen": sorted(seen),
            "expected": ["node-a", "node-b"],
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0
    finally:
        for proc in workers:
            if proc.poll() is None:
                proc.terminate()
        for proc in workers:
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()

        if started_here and nats_proc is not None:
            nats_proc.terminate()
            try:
                nats_proc.wait(timeout=3)
            except Exception:
                nats_proc.kill()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NATS multi-node integration test")
    sub = parser.add_subparsers(dest="mode", required=True)

    worker = sub.add_parser("worker")
    worker.add_argument("--node-id", required=True)
    worker.add_argument("--run-id", required=True)
    worker.add_argument("--nats-url", default="nats://127.0.0.1:4222")

    coordinator = sub.add_parser("coordinator")
    coordinator.add_argument("--nats-url", default="nats://127.0.0.1:4222")
    coordinator.add_argument("--timeout", type=float, default=12.0)
    coordinator.add_argument("--start-server", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "worker":
        code = asyncio.run(_worker(node_id=args.node_id, run_id=args.run_id, nats_url=args.nats_url))
        raise SystemExit(code)

    if args.mode == "coordinator":
        code = asyncio.run(
            _coordinator(
                nats_url=args.nats_url,
                timeout_s=args.timeout,
                start_server=args.start_server,
            )
        )
        raise SystemExit(code)


if __name__ == "__main__":
    main()
