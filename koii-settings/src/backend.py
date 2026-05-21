"""
Backend integration module for Koii Settings.
Connects to the Koii OS core system at /opt/aios/src/koii_os/
"""

import os
import sys
import json
import logging
from urllib import request
from urllib.error import URLError
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add Koii OS to Python path if available
KOII_OS_PATH = Path("/opt/aios/src")
if KOII_OS_PATH.exists():
    sys.path.insert(0, str(KOII_OS_PATH))

logger = logging.getLogger(__name__)
CONTROL_API_URL = os.getenv("KOII_CONTROL_API_URL", "http://127.0.0.1:8000")


class KoiiBackend:
    """Main backend interface for Koii OS integration."""
    
    def __init__(self):
        self.koii_available = self._check_koii_availability()
        self._kernel = None
        self._scheduler = None
        self._agent_registry = None
        
        if self.koii_available:
            self._initialize_koii_modules()
    
    def _check_koii_availability(self) -> bool:
        """Check if Koii OS modules are available."""
        try:
            import koii_os  # type: ignore[import-not-found] # noqa: F401
            return True
        except ImportError:
            logger.warning("Koii OS modules not found. Running in standalone mode.")
            return False
    
    def _initialize_koii_modules(self):
        """Initialize Koii OS core modules."""
        try:
            from koii_os.core.kernel import KernelRuntime  # type: ignore[import-not-found]
            from koii_os.core.scheduler import AgentScheduler  # type: ignore[import-not-found]
            from koii_os.llm.registry import LLMRegistry  # type: ignore[import-not-found]
            from koii_os.security.policy import SecurityPolicyEngine  # type: ignore[import-not-found]
            from koii_os.state.store import EventStore  # type: ignore[import-not-found]
            
            # Initialize dependencies
            event_store = EventStore(backend="memory")
            security_engine = SecurityPolicyEngine(
                agent_roles={},
                agent_attrs={},
                zero_trust=False  # Relaxed for settings app
            )
            llm_registry = LLMRegistry()
            
            # Initialize scheduler with dependencies
            self._scheduler = AgentScheduler(max_agents=10, state_store=event_store)
            
            # Initialize kernel with all dependencies
            self._kernel = KernelRuntime(
                scheduler=self._scheduler,
                security=security_engine,
                llm_registry=llm_registry
            )
            
            self._agent_registry = llm_registry
            
            logger.info("Koii OS modules initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Koii OS modules: {e}")
            self.koii_available = False
    
    # Agent Management
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get list of all agents with their status."""
        api_agents = self._api_get("/api/agents/status")
        if api_agents and isinstance(api_agents.get("agents"), list):
            return [self._normalize_agent(row) for row in api_agents["agents"]]

        if not self.koii_available:
            return self._get_mock_agents()
        
        try:
            # TODO: Implement actual agent retrieval from Koii OS
            agents = []
            # agents = self._agent_registry.list_agents()
            return agents
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            return []
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for a specific agent."""
        if not self.koii_available:
            return self._get_mock_agent_stats(agent_id)
        
        try:
            # TODO: Implement actual stats retrieval
            return {}
        except Exception as e:
            logger.error(f"Failed to get agent stats: {e}")
            return {}
    
    def start_agent(self, agent_id: str) -> bool:
        """Start an agent."""
        if not self.koii_available:
            logger.info(f"Mock: Starting agent {agent_id}")
            return True
        
        try:
            # TODO: Implement actual agent start
            return True
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            return False
    
    def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent."""
        if not self.koii_available:
            logger.info(f"Mock: Stopping agent {agent_id}")
            return True
        
        try:
            # TODO: Implement actual agent stop
            return True
        except Exception as e:
            logger.error(f"Failed to stop agent: {e}")
            return False
    
    def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent."""
        return self.stop_agent(agent_id) and self.start_agent(agent_id)
    
    # Task Management
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get list of all tasks."""
        api_tasks = self._api_get("/api/tasks")
        if api_tasks and isinstance(api_tasks.get("tasks"), list):
            return api_tasks["tasks"]

        if not self.koii_available:
            return self._get_mock_tasks()
        
        try:
            # TODO: Implement actual task retrieval
            return []
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []
    
    def create_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """Create a new task."""
        api_result = self._api_post("/api/tasks", task_data)
        if api_result and api_result.get("status") == "ok":
            return str(api_result.get("task_id") or "api-task")

        if not self.koii_available:
            logger.info(f"Mock: Creating task {task_data.get('name')}")
            return "mock-task-id"
        
        try:
            # TODO: Implement actual task creation
            return None
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if not self.koii_available:
            logger.info(f"Mock: Cancelling task {task_id}")
            return True
        
        try:
            # TODO: Implement actual task cancellation
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False
    
    # System Information
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        mode = self._api_get("/api/settings/mode") or {}
        resources = self._api_get("/api/resources") or {}
        if mode or resources:
            return {
                "mode": mode.get("mode", {}),
                "agents": mode.get("agents", {}),
                "resources": resources,
            }

        if not self.koii_available:
            return self._get_mock_system_status()
        
        try:
            # TODO: Implement actual system status retrieval
            return {}
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {}
    
    def get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage."""
        resources = self._api_get("/api/resources")
        if resources and resources.get("status") in (None, "ok"):
            nodes = resources.get("nodes", [])
            if nodes:
                cpu_total = sum(float(n.get("cpu_total", 0)) for n in nodes)
                cpu_used = sum(float(n.get("cpu_used", 0)) for n in nodes)
                mem_total = sum(float(n.get("memory_total_mb", 0)) for n in nodes)
                mem_used = sum(float(n.get("memory_used_mb", 0)) for n in nodes)
                return {
                    "cpu": (cpu_used / cpu_total * 100.0) if cpu_total else 0.0,
                    "memory": (mem_used / mem_total * 100.0) if mem_total else 0.0,
                    "disk": 0.0,
                    "network": 0.0,
                }

        if not self.koii_available:
            return {
                "cpu": 45.2,
                "memory": 62.8,
                "disk": 38.5,
                "network": 12.3
            }
        
        try:
            # TODO: Implement actual resource monitoring
            return {}
        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return {}
    
    # Security & Logs
    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs."""
        if not self.koii_available:
            return self._get_mock_audit_logs(limit)
        
        try:
            # TODO: Implement actual log retrieval
            return []
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    def get_security_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get security events."""
        if not self.koii_available:
            return []
        
        try:
            # TODO: Implement actual security event retrieval
            return []
        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []

    def get_llm_settings(self) -> Dict[str, Any]:
        """Read LLM settings from the control plane if it is running."""
        return self._api_get("/api/settings/llm") or {}

    def update_llm_settings(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Update non-secret LLM settings through the control plane."""
        return self._api_put("/api/settings/llm", values) or {"status": "offline"}

    def update_mode_settings(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Update Koii OS mode and built-in agent toggles."""
        return self._api_put("/api/settings/mode", values) or {"status": "offline"}

    def _api_get(self, path: str) -> Optional[Dict[str, Any]]:
        return self._api_request("GET", path)

    def _api_post(self, path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._api_request("POST", path, payload)

    def _api_put(self, path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._api_request("PUT", path, payload)

    def _api_request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        url = f"{CONTROL_API_URL.rstrip('/')}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        try:
            req = request.Request(url=url, method=method, data=data, headers=headers)
            with request.urlopen(req, timeout=1.5) as res:
                return json.loads(res.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError):
            return None

    def _normalize_agent(self, row: Dict[str, Any]) -> Dict[str, Any]:
        status = row.get("status", "unknown")
        return {
            "id": row.get("agent_id") or row.get("id") or row.get("name", "agent"),
            "name": row.get("name") or row.get("agent_id") or "Agent",
            "type": row.get("type", "task"),
            "status": "running" if status in ("enabled", "running") else status,
            "task_count": int(row.get("task_count", 0)),
            "tasks_completed": int(row.get("tasks_completed", 0)),
            "cpu_usage": float(row.get("cpu_usage", 0.0)),
            "memory_mb": int(row.get("memory_mb", 0)),
            "capabilities": list(row.get("capabilities", [])),
        }
    
    # Mock data methods for standalone mode
    def _get_mock_agents(self) -> List[Dict[str, Any]]:
        """Return mock agent data for testing."""
        return [
            {
                "id": "plugin-development-agent",
                "name": "Plugin Development Agent",
                "type": "plugin",
                "status": "running",
                "initiative_score": 0.72,
                "tasks_completed": 0,
                "task_count": 0,
                "cpu_usage": 0.0,
                "uptime": 0,
            },
            {
                "id": "core-settings-agent",
                "name": "Core Settings Agent",
                "type": "system",
                "status": "running",
                "initiative_score": 0.66,
                "tasks_completed": 0,
                "task_count": 0,
                "cpu_usage": 0.0,
                "uptime": 0,
            },
            {
                "id": "mode-settings-agent",
                "name": "Mode Settings Agent",
                "type": "mode",
                "status": "running",
                "initiative_score": 0.6,
                "tasks_completed": 0,
                "task_count": 0,
                "cpu_usage": 0.0,
                "uptime": 0,
            },
            {
                "id": "browser-agent-1",
                "name": "Browser Agent",
                "type": "browser",
                "status": "running",
                "initiative_score": 0.75,
                "tasks_completed": 42,
                "uptime": 3600
            },
            {
                "id": "task-agent-1",
                "name": "Task Coordinator",
                "type": "coordinator",
                "status": "running",
                "initiative_score": 0.85,
                "tasks_completed": 128,
                "uptime": 7200
            },
            {
                "id": "llm-agent-1",
                "name": "LLM Provider",
                "type": "llm",
                "status": "idle",
                "initiative_score": 0.60,
                "tasks_completed": 256,
                "uptime": 14400
            }
        ]
    
    def _get_mock_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Return mock agent statistics."""
        return {
            "requests_total": 1234,
            "requests_success": 1180,
            "requests_failed": 54,
            "avg_response_time": 0.45,
            "memory_usage": 128.5,
            "cpu_usage": 23.4
        }
    
    def _get_mock_tasks(self) -> List[Dict[str, Any]]:
        """Return mock task data."""
        return [
            {
                "id": "task-001",
                "name": "Web Research",
                "status": "running",
                "progress": 65,
                "agent": "browser-agent-1",
                "created": "2026-05-20T10:00:00Z"
            },
            {
                "id": "task-002",
                "name": "Data Analysis",
                "status": "completed",
                "progress": 100,
                "agent": "task-agent-1",
                "created": "2026-05-20T09:30:00Z"
            }
        ]
    
    def _get_mock_system_status(self) -> Dict[str, Any]:
        """Return mock system status."""
        return {
            "status": "healthy",
            "uptime": 86400,
            "agents_active": 3,
            "agents_total": 5,
            "tasks_running": 2,
            "tasks_queued": 1
        }
    
    def _get_mock_audit_logs(self, limit: int) -> List[Dict[str, Any]]:
        """Return mock audit logs."""
        return [
            {
                "timestamp": "2026-05-20T10:05:00Z",
                "level": "info",
                "component": "agent-manager",
                "message": "Agent browser-agent-1 started successfully",
                "user": "system"
            },
            {
                "timestamp": "2026-05-20T10:03:00Z",
                "level": "warning",
                "component": "task-scheduler",
                "message": "Task queue approaching capacity (85%)",
                "user": "system"
            },
            {
                "timestamp": "2026-05-20T10:00:00Z",
                "level": "info",
                "component": "security",
                "message": "User authentication successful",
                "user": "admin"
            }
        ]


# Global backend instance
_backend_instance: Optional[KoiiBackend] = None


def get_backend() -> KoiiBackend:
    """Get or create the global backend instance."""
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = KoiiBackend()
    return _backend_instance

# Made with Bob
