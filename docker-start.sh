#!/bin/bash
# Koii OS (AIOS) Docker Quick Start Script
# Linux/macOS

set -e

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed!"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "[ERROR] Docker is not running! Please start Docker and try again."
    exit 1
fi

# Detect docker compose command
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "[ERROR] Docker Compose is not available!"
    exit 1
fi

# Create directories
mkdir -p data logs config

# Create default agent-config.yaml if missing
if [ ! -f "agent-config.yaml" ]; then
    echo "[INFO] Creating default agent-config.yaml..."
    cat > agent-config.yaml << 'EOF'
kernel:
  max_agents: 10000
  tick_ms: 1

llm:
  default_provider: mock
  providers:
    mock:
      type: mock

agents:
  - name: system-monitor
    type: system
    roles: [monitor]

persistence:
  backend: sqlite
  sqlite:
    path: data/koii_os.db

transport:
  type: inmemory

security:
  zero_trust: true
EOF
fi

# Create .env template if missing
if [ ! -f ".env" ]; then
    echo "[INFO] Creating .env template..."
    cat > .env << 'EOF'
# Koii OS Environment Configuration
# Add your API keys here

# Anthropic API Key (for LLM chat)
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# OpenAI API Key (optional)
# OPENAI_API_KEY=sk-proj-your-key-here

# NATS Configuration (optional)
# NATS_URL=nats://nats:4222

# Browser Configuration (optional)
# KOII_BROWSER_BACKEND=playwright
EOF
fi

BROWSER_DIR="src/koii_os/browser/core"

build_browser_native() {
    echo ""
    echo "[INFO] Building Koii OS Browser (Native)..."
    echo "This may take 3-5 minutes. Please wait."
    echo ""

    if ! command -v node &> /dev/null; then
        echo "[ERROR] Node.js is not installed! Install from https://nodejs.org"
        return 1
    fi

    cd "$BROWSER_DIR"

    if [ ! -d "node_modules" ]; then
        echo "[INFO] Installing dependencies..."
        npm install
    fi

    echo "[INFO] Building browser..."
    npm run build

    echo "[INFO] Packaging for distribution..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        npx electron-builder --mac --publish=never
        echo "[SUCCESS] Browser built: dist/Koii OS Browser.app"
    else
        npx electron-builder --linux --publish=never
        echo "[SUCCESS] Browser built: dist/"
    fi

    cd - > /dev/null
}

launch_browser_native() {
    echo ""
    cd "$BROWSER_DIR"
    if [ ! -d "node_modules" ]; then
        echo "[INFO] Installing dependencies..."
        npm install
    fi

    echo "[INFO] Launching Koii OS Browser (Native)..."
    npx electron . &
    cd - > /dev/null
    echo "[SUCCESS] Browser launched!"
}

build_browser_docker() {
    echo ""
    echo "[INFO] Building Koii OS Browser (Docker)..."
    echo ""

    if ! command -v docker &> /dev/null; then
        echo "[ERROR] Docker is not installed!"
        return 1
    fi

    echo "[INFO] Building browser Docker image..."
    docker build -f Dockerfile.browser -t koii-browser:latest .
    echo "[SUCCESS] Browser Docker image built!"
}

launch_browser_docker() {
    echo ""
    echo "[INFO] Starting Koii OS Browser in Docker..."
    echo ""

    if ! $COMPOSE_CMD ps koii-browser &>/dev/null; then
        $COMPOSE_CMD up -d koii-browser
        echo "[SUCCESS] Browser started in Docker!"
        echo "Access browser at: http://localhost:3000"
    else
        echo "[INFO] Browser already running"
        echo "Access at: http://localhost:3000"
    fi
}

menu() {
    while true; do
        clear
        echo ""
        echo "========================================"
        echo "   Koii OS (AIOS) Control Center v2.0"
        echo "========================================"
        echo ""
        echo "=== Browser (Koii OS) ==="
        echo "20) Launch Browser (Native)"
        echo "21) Build Browser (Native)"
        echo "22) Launch Browser (Docker)"
        echo "23) Build Browser (Docker)"
        echo ""
        echo "=== Docker Services ==="
        echo "1) Start AIOS (with Browser & Services)"
        echo "2) Stop AIOS"
        echo "3) Restart AIOS"
        echo "4) View logs"
        echo "5) Rebuild containers"
        echo "6) Clean up (remove containers and volumes)"
        echo "7) Show status"
        echo "8) Open Web UI"
        echo "9) Enter container shell (AIOS)"
        echo "10) Browser container shell"
        echo ""
        echo "=== Browser-specific ==="
        echo "11) View Browser logs"
        echo "12) Rebuild Browser only"
        echo "13) Restart Browser container"
        echo ""
        echo "0) Exit"
        echo ""
        read -rp "Select an option: " choice

        case $choice in
            20)
                launch_browser_native
                read -rp "Press Enter to continue..."
                ;;
            21)
                build_browser_native
                read -rp "Press Enter to continue..."
                ;;
            22)
                launch_browser_docker
                read -rp "Press Enter to continue..."
                ;;
            23)
                build_browser_docker
                read -rp "Press Enter to continue..."
                ;;
            1)
                echo ""
                echo "[INFO] Starting Koii OS with Browser..."
                $COMPOSE_CMD up -d
                echo ""
                echo "[SUCCESS] Services are running!"
                echo "AIOS Web UI: http://localhost:8000"
                echo "Browser UI: http://localhost:3000"
                echo "NATS Monitor: http://localhost:8222"
                read -rp "Press Enter to continue..."
                ;;
            2)
                echo ""
                echo "[INFO] Stopping Koii OS..."
                $COMPOSE_CMD down
                echo "[SUCCESS] Koii OS stopped"
                read -rp "Press Enter to continue..."
                ;;
            3)
                echo ""
                echo "[INFO] Restarting Koii OS..."
                $COMPOSE_CMD restart
                echo "[SUCCESS] Koii OS restarted"
                read -rp "Press Enter to continue..."
                ;;
            4)
                echo ""
                echo "[INFO] Viewing logs (Ctrl+C to exit)..."
                $COMPOSE_CMD logs -f
                ;;
            5)
                echo ""
                echo "[INFO] Rebuilding containers..."
                $COMPOSE_CMD down
                $COMPOSE_CMD build --no-cache
                $COMPOSE_CMD up -d
                echo "[SUCCESS] Containers rebuilt and started"
                read -rp "Press Enter to continue..."
                ;;
            6)
                echo ""
                echo "[WARNING] This will remove all containers, volumes, and data!"
                read -rp "Are you sure? (yes/no): " confirm
                if [[ "$confirm" == "yes" ]]; then
                    echo "[INFO] Cleaning up..."
                    $COMPOSE_CMD down -v
                    echo "[SUCCESS] Cleanup complete"
                else
                    echo "Cleanup cancelled"
                fi
                read -rp "Press Enter to continue..."
                ;;
            7)
                echo ""
                echo "[INFO] Service Status:"
                $COMPOSE_CMD ps
                read -rp "Press Enter to continue..."
                ;;
            8)
                echo ""
                echo "[INFO] Opening AIOS Web UI..."
                if command -v xdg-open &> /dev/null; then
                    xdg-open http://localhost:8000
                elif command -v open &> /dev/null; then
                    open http://localhost:8000
                else
                    echo "Open http://localhost:8000 in your browser"
                fi
                read -rp "Press Enter to continue..."
                ;;
            9)
                echo ""
                echo "[INFO] Entering AIOS container shell..."
                docker exec -it koii-aios /bin/bash
                read -rp "Press Enter to continue..."
                ;;
            10)
                echo ""
                echo "[INFO] Entering Browser container shell..."
                docker exec -it koii-browser /bin/bash
                read -rp "Press Enter to continue..."
                ;;
            11)
                echo ""
                echo "[INFO] Browser logs (Ctrl+C to exit)..."
                $COMPOSE_CMD logs -f koii-browser
                ;;
            12)
                echo ""
                echo "[INFO] Rebuilding Browser container..."
                $COMPOSE_CMD build --no-cache koii-browser
                echo "[SUCCESS] Browser rebuilt"
                read -rp "Press Enter to continue..."
                ;;
            13)
                echo ""
                echo "[INFO] Restarting Browser..."
                $COMPOSE_CMD restart koii-browser
                echo "[SUCCESS] Browser restarted"
                read -rp "Press Enter to continue..."
                ;;
            0)
                echo ""
                echo "Goodbye!"
                exit 0
                ;;
            *)
                echo "Invalid option. Please try again."
                sleep 1
                ;;
        esac
    done
}

menu
