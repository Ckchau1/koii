#!/bin/bash
# Build script for Koii Settings

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build"

echo "=== Building Koii Settings ==="
echo "Project directory: $PROJECT_DIR"
echo "Build directory: $BUILD_DIR"
echo ""

# Check for required tools
echo "Checking dependencies..."
MISSING_DEPS=()

if ! command -v meson &> /dev/null; then
    MISSING_DEPS+=("meson")
fi

if ! command -v ninja &> /dev/null; then
    MISSING_DEPS+=("ninja-build")
fi

if ! command -v python3 &> /dev/null; then
    MISSING_DEPS+=("python3")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo "Error: Missing required dependencies:"
    printf '  - %s\n' "${MISSING_DEPS[@]}"
    echo ""
    echo "Install them with:"
    echo "  sudo apt install ${MISSING_DEPS[*]}"
    exit 1
fi

echo "✓ All dependencies found"
echo ""

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

# Setup build directory
echo "Setting up build directory..."
cd "$PROJECT_DIR"
meson setup "$BUILD_DIR" --prefix=/usr

echo "✓ Build configured"
echo ""

# Compile
echo "Compiling..."
meson compile -C "$BUILD_DIR"

echo "✓ Compilation complete"
echo ""

# Run tests (if any)
if meson test -C "$BUILD_DIR" --list 2>/dev/null | grep -q .; then
    echo "Running tests..."
    meson test -C "$BUILD_DIR" || true
    echo ""
fi

echo "=== Build Complete ==="
echo ""
echo "To install, run:"
echo "  sudo meson install -C $BUILD_DIR"
echo ""
echo "Or to create a package:"
echo "  cd $BUILD_DIR"
echo "  DESTDIR=\$PWD/install-root meson install"
echo "  # Then create .deb or .rpm from install-root/"
echo ""

# Made with Bob
