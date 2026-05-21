from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..state.store import EventStore


@dataclass
class ResourceNode:
    node_id: str
    region: str
    cpu_total: int
    cpu_used: int
    memory_total_mb: int
    memory_used_mb: int
    gpu_total: int = 0
    gpu_used: int = 0

    @property
    def cpu_available(self) -> int:
        return max(0, self.cpu_total - self.cpu_used)

    @property
    def memory_available_mb(self) -> int:
        return max(0, self.memory_total_mb - self.memory_used_mb)

    @property
    def gpu_available(self) -> int:
        return max(0, self.gpu_total - self.gpu_used)


class GlobalResourceManager:
    def __init__(self, state_store: EventStore | None = None) -> None:
        self.state_store = state_store
        self.nodes: dict[str, ResourceNode] = {}

    def load_nodes(self, cfg: dict[str, Any]) -> None:
        for item in cfg.get("nodes", []):
            node = ResourceNode(
                node_id=str(item["id"]),
                region=str(item.get("region", "unknown")),
                cpu_total=int(item.get("cpu_total", 0)),
                cpu_used=int(item.get("cpu_used", 0)),
                memory_total_mb=int(item.get("memory_total_mb", 0)),
                memory_used_mb=int(item.get("memory_used_mb", 0)),
                gpu_total=int(item.get("gpu_total", 0)),
                gpu_used=int(item.get("gpu_used", 0)),
            )
            self.nodes[node.node_id] = node

    def reserve(
        self,
        cpu: int,
        memory_mb: int,
        gpu: int = 0,
        preferred_region: str | None = None,
    ) -> dict[str, Any]:
        candidates = list(self.nodes.values())
        if preferred_region:
            preferred = [n for n in candidates if n.region == preferred_region]
            if preferred:
                candidates = preferred

        # Keep the policy deterministic: most available CPU first.
        candidates.sort(key=lambda n: (n.cpu_available, n.memory_available_mb, n.gpu_available), reverse=True)

        for node in candidates:
            if node.cpu_available >= cpu and node.memory_available_mb >= memory_mb and node.gpu_available >= gpu:
                node.cpu_used += cpu
                node.memory_used_mb += memory_mb
                node.gpu_used += gpu
                result = {
                    "status": "ok",
                    "node_id": node.node_id,
                    "region": node.region,
                    "reserved": {"cpu": cpu, "memory_mb": memory_mb, "gpu": gpu},
                }
                self._append_event("resource.reserved", result)
                return result

        result = {
            "status": "error",
            "reason": "no node satisfies requested resources",
            "requested": {"cpu": cpu, "memory_mb": memory_mb, "gpu": gpu},
            "preferred_region": preferred_region,
        }
        self._append_event("resource.reserve_failed", result)
        return result

    def release(self, node_id: str, cpu: int, memory_mb: int, gpu: int = 0) -> dict[str, Any]:
        node = self.nodes.get(node_id)
        if node is None:
            return {"status": "error", "reason": f"unknown node {node_id}"}

        node.cpu_used = max(0, node.cpu_used - cpu)
        node.memory_used_mb = max(0, node.memory_used_mb - memory_mb)
        node.gpu_used = max(0, node.gpu_used - gpu)
        result = {
            "status": "ok",
            "node_id": node_id,
            "released": {"cpu": cpu, "memory_mb": memory_mb, "gpu": gpu},
        }
        self._append_event("resource.released", result)
        return result

    def overview(self) -> dict[str, Any]:
        fleet = [
            {
                "node_id": n.node_id,
                "region": n.region,
                "cpu": {"total": n.cpu_total, "used": n.cpu_used, "available": n.cpu_available},
                "memory_mb": {
                    "total": n.memory_total_mb,
                    "used": n.memory_used_mb,
                    "available": n.memory_available_mb,
                },
                "gpu": {"total": n.gpu_total, "used": n.gpu_used, "available": n.gpu_available},
            }
            for n in self.nodes.values()
        ]
        return {"status": "ok", "nodes": fleet}

    def _append_event(self, topic: str, payload: dict[str, Any]) -> None:
        if self.state_store is not None:
            self.state_store.append(topic, payload)
