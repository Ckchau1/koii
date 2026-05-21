from __future__ import annotations


class SecurityPolicyEngine:
    def __init__(
        self,
        agent_roles: dict[str, list[str]],
        agent_attrs: dict[str, dict[str, object]],
        zero_trust: bool = True,
    ) -> None:
        self.agent_roles = agent_roles
        self.agent_attrs = agent_attrs
        self.zero_trust = zero_trust

    def authorize(
        self,
        agent_id: str,
        action: str,
        resource: str,
        required_role: str | None = None,
        required_attr: tuple[str, object] | None = None,
    ) -> bool:
        if not self.zero_trust:
            return True

        roles = self.agent_roles.get(agent_id, [])
        attrs = self.agent_attrs.get(agent_id, {})

        if required_role is not None and required_role not in roles:
            return False
        if required_attr is not None:
            key, expected = required_attr
            if attrs.get(key) != expected:
                return False

        return self._action_allowed(action, resource, roles)

    def authorize_model_call(self, agent_id: str, model_name: str) -> bool:
        return self.authorize(
            agent_id=agent_id,
            action="invoke",
            resource=f"model:{model_name}",
            required_role=None,
        )

    def authorize_os_action(self, agent_id: str, command: str) -> bool:
        return self.authorize(
            agent_id=agent_id,
            action="execute",
            resource=f"os:{command.split(' ', 1)[0] if command else 'unknown'}",
            required_role="orchestrator",
        )

    @staticmethod
    def _action_allowed(action: str, resource: str, roles: list[str]) -> bool:
        policy = {
            "orchestrator": {"invoke", "delegate", "read", "write", "execute"},
            "worker": {"invoke", "read"},
            "compute": {"invoke", "read"},
            "system": {"read", "write", "monitor", "execute"},
        }

        allowed_actions = set()
        for role in roles:
            allowed_actions.update(policy.get(role, set()))

        if action not in allowed_actions:
            return False

        # Simple micro-segmentation simulation.
        if resource.startswith("system:") and "system" not in roles:
            return False
        return True
