#!/bin/bash

# Koii OS Browser - Build Script for Linux/macOS
# Creates standalone executables for distribution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
OS_TYPE="$(uname -s)"
case "${OS_TYPE}" in
    Linux*)     OS="Linux";;
    Darwin*)    OS="macOS";;
    *)          OS="UNKNOWN";;
esac

echo ""
echo "========================================"
echo -e "${BLUE} Koii OS Browser - Build Script${NC}"
echo -e "${BLUE} OS: $OS${NC}"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed!${NC}"
    echo "Install from: https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${BLUE}[INFO] Node.js version: $NODE_VERSION${NC}"

# Check npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}[ERROR] npm is not installed!${NC}"
    exit 1
fi

# Menu function
menu() {
    while true; do
        clear
        echo ""
        echo "========================================"
        echo "       Build Options"
        echo "========================================"
        echo ""
        echo "1) Install dependencies (first time only)"
        echo "2) Build React app only"
        echo "3) Build for $OS"
        echo "4) Build for all platforms"
        echo "5) Clean build (remove build/dist folders)"
        echo "6) Full clean and rebuild"
        echo "7) Run app in Electron (dev mode)"
        echo ""
        echo "0) Exit"
        echo ""
        read -rp "Select an option: " choice

        case $choice in
            1) install_deps ;;
            2) build_react ;;
            3) build_for_os ;;
            4) build_all ;;
            5) clean_build ;;
            6) full_clean ;;
            7) dev_run ;;
            0) exit_script ;;
            *) echo "Invalid option. Please try again."; sleep 1 ;;
        esac
    done
}

# Install dependencies
install_deps() {
    echo ""
    echo -e "${BLUE}[INFO] Installing dependencies...${NC}"
    echo "This may take 5-10 minutes. Please wait."
    echo ""
    npm install
    echo ""
    echo -e "${GREEN}[SUCCESS] Dependencies installed!${NC}"
    read -rp "Press Enter to continue..."
}

# Build React app
build_react() {
    echo ""
    echo -e "${BLUE}[INFO] Building React application...${NC}"
    echo "This may take 2-3 minutes. Please wait."
    echo ""
    npm run build
    echo ""
    echo -e "${GREEN}[SUCCESS] React build complete!${NC}"
    echo "Output: build/"
    read -rp "Press Enter to continue..."
}

# Build for current OS
build_for_os() {
    echo ""
    echo -e "${BLUE}[INFO] Building for $OS...${NC}"
    echo "This may take 3-5 minutes. Please wait."
    echo ""

    # Build React if not already built
    if [ ! -d "build" ]; then
        echo -e "${BLUE}[INFO] React app not built yet. Building now...${NC}"
        npm run build
    fi

    case "${OS}" in
        macOS)
            echo -e "${BLUE}[INFO] Creating macOS app...${NC}"
            npm run dist:mac
            echo ""
            echo -e "${GREEN}[SUCCESS] macOS app created!${NC}"
            echo "Outputs:"
            echo "  - DMG: dist/Koii OS Browser-0.1.0.dmg"
            echo "  - ZIP: dist/Koii OS Browser-0.1.0.zip"
            ;;
        Linux)
            echo -e "${BLUE}[INFO] Creating Linux apps...${NC}"
            npm run dist:linux
            echo ""
            echo -e "${GREEN}[SUCCESS] Linux apps created!${NC}"
            echo "Outputs:"
            echo "  - AppImage: dist/Koii OS Browser-0.1.0.AppImage"
            echo "  - DEB: dist/Koii OS Browser-0.1.0.deb"
            ;;
        *)
            echo -e "${RED}[ERROR] Unknown OS: $OS${NC}"
            ;;
    esac

    read -rp "Press Enter to continue..."
}

# Build for all platforms
build_all() {
    echo ""
    echo -e "${BLUE}[INFO] Building for all platforms...${NC}"
    echo "This may take 10-15 minutes. Please wait."
    echo ""

    # Build React
    echo -e "${BLUE}[INFO] Building React...${NC}"
    npm run build
    echo ""

    # Build for Windows
    echo -e "${BLUE}[INFO] Building for Windows...${NC}"
    npm run dist:win
    echo ""

    # Build for macOS
    echo -e "${BLUE}[INFO] Building for macOS...${NC}"
    npm run dist:mac
    echo ""

    # Build for Linux
    echo -e "${BLUE}[INFO] Building for Linux...${NC}"
    npm run dist:linux
    echo ""

    echo -e "${GREEN}[SUCCESS] All platforms built!${NC}"
    echo ""
    echo "Outputs in dist/ folder:"
    echo "  Windows: Koii OS Browser-0.1.0.exe"
    echo "  macOS: Koii OS Browser-0.1.0.dmg"
    echo "  Linux: Koii OS Browser-0.1.0.AppImage"
    echo ""

    read -rp "Press Enter to continue..."
}

# Clean build
clean_build() {
    echo ""
    echo -e "${BLUE}[INFO] Cleaning build and dist folders...${NC}"
    echo ""

    if [ -d "build" ]; then
        echo "Removing build folder..."
        rm -rf build
        echo -e "${GREEN}[OK] build/ removed${NC}"
    fi

    if [ -d "dist" ]; then
        echo "Removing dist folder..."
        rm -rf dist
        echo -e "${GREEN}[OK] dist/ removed${NC}"
    fi

    echo ""
    echo -e "${GREEN}[SUCCESS] Cleanup complete!${NC}"
    read -rp "Press Enter to continue..."
}

# Full clean and rebuild
full_clean() {
    echo ""
    echo -e "${YELLOW}[WARNING] This will remove node_modules, build, and dist!${NC}"
    echo ""
    read -rp "Are you sure? Type 'yes' to continue: " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        read -rp "Press Enter to continue..."
        return
    fi

    echo ""
    echo -e "${BLUE}[INFO] Performing full cleanup...${NC}"

    if [ -d "node_modules" ]; then
        echo "Removing node_modules..."
        rm -rf node_modules
        echo -e "${GREEN}[OK] node_modules/ removed${NC}"
    fi

    if [ -d "build" ]; then
        echo "Removing build folder..."
        rm -rf build
        echo -e "${GREEN}[OK] build/ removed${NC}"
    fi

    if [ -d "dist" ]; then
        echo "Removing dist folder..."
        rm -rf dist
        echo -e "${GREEN}[OK] dist/ removed${NC}"
    fi

    echo ""
    echo -e "${BLUE}[INFO] Reinstalling dependencies...${NC}"
    npm install
    echo ""

    echo -e "${BLUE}[INFO] Building React app...${NC}"
    npm run build
    echo ""

    echo -e "${GREEN}[SUCCESS] Full rebuild complete!${NC}"
    read -rp "Press Enter to continue..."
}

# Dev run
dev_run() {
    echo ""
    echo -e "${BLUE}[INFO] Starting Koii OS Browser in development mode...${NC}"
    echo ""
    echo "This will:"
    echo "1. Start React dev server on port 3000"
    echo "2. Launch Electron window"
    echo "3. Auto-reload on code changes"
    echo ""
    echo "Press Ctrl+C to stop."
    echo ""
    npm run dev
    echo ""
    read -rp "Press Enter to continue..."
}

# Exit script
exit_script() {
    echo ""
    echo -e "${GREEN}Thank you for using Koii OS Browser!${NC}"
    echo ""
    exit 0
}

# Run menu
menu
