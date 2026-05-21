#!/usr/bin/env bash
# Create AI Browser desktop application
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${1:-/opt/aios}"

echo "=== Creating AI Browser Desktop Application ==="

# Create desktop file
cat > /tmp/koii-ai-browser.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Koii AI Browser
GenericName=AI-Powered Web Browser
Comment=Intelligent web browser with AI automation capabilities
Exec=/opt/aios/scripts/launch-ai-browser.sh
Icon=web-browser
Terminal=false
Categories=Network;WebBrowser;
Keywords=browser;web;internet;ai;automation;
StartupNotify=true
StartupWMClass=koii-ai-browser
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
Actions=NewWindow;NewPrivateWindow;

[Desktop Action NewWindow]
Name=Open a New Window
Exec=/opt/aios/scripts/launch-ai-browser.sh --new-window

[Desktop Action NewPrivateWindow]
Name=Open a New Private Window
Exec=/opt/aios/scripts/launch-ai-browser.sh --private-window
EOF

# Create launcher script
cat > /tmp/launch-ai-browser.sh << 'EOF'
#!/usr/bin/env bash
# Launcher for Koii AI Browser

set -euo pipefail

AIOS_DIR="/opt/aios"
ELECTRON_DIR="$AIOS_DIR/electron"
LOG_FILE="$HOME/.local/share/koii/ai-browser.log"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Check if Electron is installed
if ! command -v electron &> /dev/null; then
    # Try to use system electron or install it
    if command -v npm &> /dev/null; then
        echo "Installing Electron..." | tee -a "$LOG_FILE"
        cd "$ELECTRON_DIR"
        npm install 2>&1 | tee -a "$LOG_FILE"
    else
        zenity --error --text="Electron is not installed and npm is not available.\n\nPlease install Node.js and npm first." 2>/dev/null || \
        notify-send "Koii AI Browser" "Electron is not installed. Please install Node.js and npm." -u critical
        exit 1
    fi
fi

# Check if electron directory exists
if [[ ! -d "$ELECTRON_DIR" ]]; then
    zenity --error --text="AI Browser files not found at $ELECTRON_DIR" 2>/dev/null || \
    notify-send "Koii AI Browser" "AI Browser files not found" -u critical
    exit 1
fi

# Launch the browser
echo "Starting Koii AI Browser..." | tee -a "$LOG_FILE"
cd "$ELECTRON_DIR"

# Parse arguments
ARGS=""
for arg in "$@"; do
    case "$arg" in
        --new-window)
            ARGS="$ARGS --new-window"
            ;;
        --private-window)
            ARGS="$ARGS --incognito"
            ;;
        *)
            ARGS="$ARGS $arg"
            ;;
    esac
done

# Start Electron app
if command -v electron &> /dev/null; then
    electron . $ARGS 2>&1 | tee -a "$LOG_FILE" &
elif command -v npm &> /dev/null; then
    npm start 2>&1 | tee -a "$LOG_FILE" &
else
    zenity --error --text="Cannot start AI Browser: Electron not found" 2>/dev/null || \
    notify-send "Koii AI Browser" "Cannot start: Electron not found" -u critical
    exit 1
fi

# Show notification
notify-send "Koii AI Browser" "AI Browser is starting..." -i web-browser 2>/dev/null || true

echo "AI Browser started successfully" | tee -a "$LOG_FILE"
EOF

chmod +x /tmp/launch-ai-browser.sh

echo "✅ AI Browser desktop application created"
echo ""
echo "Files created:"
echo "  - /tmp/koii-ai-browser.desktop"
echo "  - /tmp/launch-ai-browser.sh"
echo ""
echo "To install:"
echo "  sudo cp /tmp/koii-ai-browser.desktop /usr/share/applications/"
echo "  sudo cp /tmp/launch-ai-browser.sh /opt/aios/scripts/"
echo "  sudo chmod +x /opt/aios/scripts/launch-ai-browser.sh"
echo "  sudo update-desktop-database /usr/share/applications/"

# Made with Bob
