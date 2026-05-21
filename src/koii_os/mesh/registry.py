from __future__ import annotations

from dataclasses import dataclass

from ..agents.base import BaseAgent


@dataclass
class AgentRecord:
    agent_id: str
    agent_type: str
    roles: list[str]
    region: str


class AgentRegistry:
    def __init__(self) -> None:
        self._records: dict[str, AgentRecord] = {}

    def register(self, agent: BaseAgent) -> None:
        record = AgentRecord(
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
            roles=list(agent.roles),
            region=str(agent.attributes.get("region", "unknown")),
        )
        self._records[agent.agent_id] = record

    def discover(self, role: str | None = None, agent_type: str | None = None) -> list[AgentRecord]:
        result = list(self._records.values())
        if role is not None:
            result = [r for r in result if role in r.roles]
        if agent_type is not None:
            result = [r for r in result if r.agent_type == agent_type]
        return result
