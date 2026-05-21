#!/bin/bash
# Koii OS (AIOS) Docker Quick Start Script
# Works on Linux, macOS, and Windows (Git Bash/WSL)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_msg "$RED" "❌ Docker is not installed!"
        print_msg "$YELLOW" "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_msg "$RED" "❌ Docker daemon is not running!"
        print_msg "$YELLOW" "Please start Docker Desktop or Docker daemon"
        exit 1
    fi
    
    print_msg "$GREEN" "✓ Docker is ready"
}

# Check if docker-compose is available
check_compose() {
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_msg "$RED" "❌ Docker Compose is not available!"
        print_msg "$YELLOW" "Please install Docker Compose"
        exit 1
    fi
    print_msg "$GREEN" "✓ Docker Compose is ready"
}

# Create necessary directories
setup_directories() {
    print_msg "$BLUE" "📁 Setting up directories..."
    mkdir -p data logs config
    
    # Create default agent-config.yaml if it doesn't exist
    if [ ! -f "agent-config.yaml" ]; then
        print_msg "$YELLOW" "⚠️  agent-config.yaml not found, creating default..."
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
    
    # Create .env template if it doesn't exist
    if [ ! -f ".env" ]; then
        print_msg "$YELLOW" "⚠️  .env not found, creating template..."
        cat > .env << 'EOF'
# Koii OS Environment Configuration
# Copy this file and add your API keys

# OpenAI API Key (optional)
# OPENAI_API_KEY=sk-proj-your-key-here

# Anthropic API Key (optional)
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# NATS Configuration (optional)
# NATS_URL=nats://nats:4222

# Browser Configuration (optional)
# KOII_BROWSER_BACKEND=playwright
EOF
    fi
    
    print_msg "$GREEN" "✓ Directories ready"
}

# Main menu
show_menu() {
    echo ""
    print_msg "$BLUE" "╔════════════════════════════════════════╗"
    print_msg "$BLUE" "║   Koii OS (AIOS) Docker Manager       ║"
    print_msg "$BLUE" "╚════════════════════════════════════════╝"
    echo ""
    echo "1) 🚀 Start AIOS (with Web UI)"
    echo "2) 🛑 Stop AIOS"
    echo "3) 🔄 Restart AIOS"
    echo "4) 📊 View logs"
    echo "5) 🔧 Rebuild containers"
    echo "6) 🧹 Clean up (remove containers and volumes)"
    echo "7) 📈 Show status"
    echo "8) 🌐 Open Web UI"
    echo "9) 💻 Enter container shell"
    echo "0) ❌ Exit"
    echo ""
}

# Start services
start_services() {
    print_msg "$GREEN" "🚀 Starting Koii OS..."
    $COMPOSE_CMD up -d
    echo ""
    print_msg "$GREEN" "✓ Koii OS is running!"
    print_msg "$BLUE" "📊 Web UI: http://localhost:8000"
    print_msg "$BLUE" "📡 NATS Monitor: http://localhost:8222"
    echo ""
    print_msg "$YELLOW" "💡 Tip: Run './docker-start.sh' again to manage services"
}

# Stop services
stop_services() {
    print_msg "$YELLOW" "🛑 Stopping Koii OS..."
    $COMPOSE_CMD down
    print_msg "$GREEN" "✓ Koii OS stopped"
}

# Restart services
restart_services() {
    print_msg "$YELLOW" "🔄 Restarting Koii OS..."
    $COMPOSE_CMD restart
    print_msg "$GREEN" "✓ Koii OS restarted"
}

# View logs
view_logs() {
    print_msg "$BLUE" "📊 Viewing logs (Ctrl+C to exit)..."
    $COMPOSE_CMD logs -f
}

# Rebuild containers
rebuild_containers() {
    print_msg "$YELLOW" "🔧 Rebuilding containers..."
    $COMPOSE_CMD down
    $COMPOSE_CMD build --no-cache
    $COMPOSE_CMD up -d
    print_msg "$GREEN" "✓ Containers rebuilt and started"
}

# Clean up
cleanup() {
    print_msg "$RED" "⚠️  This will remove all containers, volumes, and data!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        print_msg "$YELLOW" "🧹 Cleaning up..."
        $COMPOSE_CMD down -v
        print_msg "$GREEN" "✓ Cleanup complete"
    else
        print_msg "$BLUE" "Cleanup cancelled"
    fi
}

# Show status
show_status() {
    print_msg "$BLUE" "📈 Service Status:"
    $COMPOSE_CMD ps
}

# Open Web UI
open_web_ui() {
    print_msg "$BLUE" "🌐 Opening Web UI..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000
    elif command -v open &> /dev/null; then
        open http://localhost:8000
    elif command -v start &> /dev/null; then
        start http://localhost:8000
    else
        print_msg "$YELLOW" "Please open http://localhost:8000 in your browser"
    fi
}

# Enter container shell
enter_shell() {
    print_msg "$BLUE" "💻 Entering container shell..."
    docker exec -it koii-aios /bin/bash
}

# Main script
main() {
    check_docker
    check_compose
    setup_directories
    
    # If arguments provided, execute directly
    if [ $# -gt 0 ]; then
        case "$1" in
            start) start_services ;;
            stop) stop_services ;;
            restart) restart_services ;;
            logs) view_logs ;;
            rebuild) rebuild_containers ;;
            clean) cleanup ;;
            status) show_status ;;
            shell) enter_shell ;;
            *)
                echo "Usage: $0 {start|stop|restart|logs|rebuild|clean|status|shell}"
                exit 1
                ;;
        esac
        exit 0
    fi
    
    # Interactive menu
    while true; do
        show_menu
        read -p "Select an option: " choice
        case $choice in
            1) start_services ;;
            2) stop_services ;;
            3) restart_services ;;
            4) view_logs ;;
            5) rebuild_containers ;;
            6) cleanup ;;
            7) show_status ;;
            8) open_web_ui ;;
            9) enter_shell ;;
            0) 
                print_msg "$GREEN" "👋 Goodbye!"
                exit 0
                ;;
            *)
                print_msg "$RED" "Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

main "$@"

# Made with Bob
