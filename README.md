# Koii OS Prototype

This repository is a practical prototype of an AI-native operating system architecture inspired by your Koii OS design.

## What this prototype includes

- AI-first microkernel-style runtime (`KernelRuntime`)
- Pluggable LLM provider registry (mock, OpenAI, Anthropic, vLLM)
- Agent scheduler with priorities, quotas, and heartbeat monitoring
- Autonomous agent types:
  - Task Agents
  - Compute Agents
  - Orchestration Agents
  - System Agents
- Multi-agent collaboration primitives:
  - Agent discovery and registration
  - Task decomposition and delegation
  - Parallel execution
  - Result synthesis
- Koii-aligned control plane primitives:
  - Global resource federation and node reservation
  - Declarative collaboration workflows
  - Autonomous goal runtime with retry and daemon polling
- **AI Browser Integration** (NEW):
  - Playwright-based browser automation
  - Autonomous web navigation, interaction, and screenshot capture
  - LLM-driven page analysis and element extraction
  - Browser actions in autonomous goal planning
- Messaging and workspace integration:
  - Telegram and WhatsApp notification channels
  - Coding workspace introspection and git-based status reporting
  - Command-line helpers for sending messages and checking workspace health
- Transport abstraction for agent messaging:
  - In-memory bus
  - HTTP relay bus (prototype mode)
- Persistence and recovery:
  - SQLite-backed event store
  - Pending task recovery on bootstrap
- Security primitives:
  - Sandbox-like policy checks
  - Zero-trust style authorization checks
  - RBAC + ABAC policy gate
- Declarative YAML config (`agent-config.yaml`)

## 🚀 Quick Start

### Option 1: Docker (推薦 - 適用所有平台)

**最簡單的方式！適用於 Windows、Linux、macOS**

1. 安裝 [Docker Desktop](https://docs.docker.com/get-docker/)

2. 啟動 AIOS：

**Windows:**
```cmd
docker-start.bat
```

**Linux/macOS:**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

3. 訪問 Web UI: http://localhost:8000

📖 詳細文檔請參閱 [DOCKER.md](DOCKER.md)

### Option 2: 本地 Python 環境

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment (optional for real LLM APIs):

```bash
# Copy the example config
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-proj-your-actual-key
# ANTHROPIC_API_KEY=sk-ant-your-actual-key
```

3. Run the demo:

```bash
python -m src.main
```

4. Use the Koii-style CLI:

```bash
# resource control
python -m src.koii_cli resource list
python -m src.koii_cli resource reserve --cpu 4 --memory-mb 4096 --region NA

# agent control
python -m src.koii_cli agent create --name research-assistant --type task --goal "Summarize latest AI multi-agent trends"
python -m src.koii_cli agent list
python -m src.koii_cli agent run research-assistant --watch

# messaging integration
python -m src.koii_cli notify telegram --message "AIOS is online"
python -m src.koii_cli notify whatsapp --message "AIOS workspace is ready"

# coding workspace introspection
python -m src.koii_cli workspace --path .
```

# Min Browser integration
To use the Electron-based Koii Min Browser host for agent browsing, install dependencies in `electron/` and start the host:

```bash
cd electron
npm install
npm start
```

Then enable the browser backend using environment variables or `.env`:

```bash
KOII_BROWSER_BACKEND=minbrowser
KOII_BROWSER_MIN_URL=http://127.0.0.1:43210
KOII_BROWSER_AGENT_TOKEN=your-secure-token
KOII_BROWSER_LAUNCH_CMD="npx electron ."
```

After starting the Electron host, Koii agents can use the local API at `http://127.0.0.1:43210/api/v1/browser`.

5. Run the Web UI Control Panel (real-time agent management & task distribution):

```bash
# Start the FastAPI server with web interface
python -m src.koii_web
```

Then open **http://localhost:8000** in your browser to:
- View all running agents and their roles
- Create new agents dynamically on-the-fly
- Schedule tasks with retry logic and assign to specific agents
- Create autonomous goals with iterative execution
- Monitor global resource usage across distributed nodes
- Stream real-time events via WebSocket
- Trigger immediate agent actions from the UI

6. Run multi-node NATS mesh integration test:

```bash
# Start local broker automatically if needed and validate cross-process messaging
python scripts/nats_multinode_integration.py coordinator --start-server
```

7. Switch transport/persistence in `agent-config.yaml`:
  - `transport.type: inmemory | http-relay | nats`
  - `persistence.backend: memory | sqlite`
  
8. Configure Koii-like global infrastructure and workflows:
  - `infrastructure.nodes`: global node pool and capacities
  - `collaboration.workflows`: workflow goals and resource requests
  - `autonomy` + `daemon`: planner loop behavior and background polling

## Browser Automation

AIOS now supports autonomous web navigation and interaction through Playwright. Agents can autonomously:
- Navigate to websites
- Take screenshots
- Extract page content and links
- Click buttons and submit forms
- Type into fields
- Execute JavaScript

**Quick example:**

```bash
# Test browser automation separately
python scripts/demo_browser_automation.py

# Or define browser-based autonomous goals in agent-config.yaml:
# autonomy:
#   goal_tasks:
#     - id: web-research-goal
#       goal: "Navigate to example.com and take a screenshot"
```

See [BROWSER_AUTOMATION.md](BROWSER_AUTOMATION.md) for detailed usage guide.

## Current scope

This is a simulation/prototype layer in Python, not a real hardware kernel. It is designed to validate architecture, APIs, and workflows before implementing low-level runtime components.

## Next milestones

- Replace in-memory messaging with gRPC/NATS/Kafka transport
- Add distributed consensus backend (Raft)
- Add full duplex relay worker and delivery acknowledgements
- Add policy engine with OPA/Rego
- Add Kubernetes operator for global orchestration
