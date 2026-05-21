#!/usr/bin/env bash
# Verify AIOS ISO contents and integration
set -euo pipefail

ISO_PATH="${1:-build/AIOS-Ubuntu-24.04.2.iso}"
WORKDIR="${2:-/tmp/aios-verify-$$}"

if [[ ! -f "$ISO_PATH" ]]; then
    echo "Error: ISO not found at $ISO_PATH"
    echo "Usage: $0 [iso-path] [work-dir]"
    exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Error: This script must be run as root"
    echo "Usage: sudo $0 [iso-path]"
    exit 1
fi

echo "=== Verifying AIOS ISO: $ISO_PATH ==="
echo ""

# Create working directory
mkdir -p "$WORKDIR"
MOUNT_DIR="$WORKDIR/mnt"
EXTRACT_DIR="$WORKDIR/extract"

mkdir -p "$MOUNT_DIR" "$EXTRACT_DIR"

# Mount ISO
echo "Mounting ISO..."
mount -o loop,ro "$ISO_PATH" "$MOUNT_DIR"

# Find squashfs
SQUASHFS=$(find "$MOUNT_DIR/casper" -maxdepth 1 -type f -name "*.squashfs" -printf '%s %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-)
if [[ -z "$SQUASHFS" ]]; then
    umount "$MOUNT_DIR"
    echo "Error: No squashfs found in ISO"
    exit 1
fi

echo "Found squashfs: $(basename $SQUASHFS)"
echo "Extracting squashfs (this may take a while)..."
unsquashfs -d "$EXTRACT_DIR" "$SQUASHFS" >/dev/null 2>&1

umount "$MOUNT_DIR"

# Verify components
echo ""
echo "=== Verification Results ==="
echo ""

check_file() {
    local path="$1"
    local desc="$2"
    if [[ -e "$EXTRACT_DIR$path" ]]; then
        echo "✅ $desc: $path"
        return 0
    else
        echo "❌ MISSING $desc: $path"
        return 1
    fi
}

check_executable() {
    local path="$1"
    local desc="$2"
    if [[ -x "$EXTRACT_DIR$path" ]]; then
        echo "✅ $desc (executable): $path"
        return 0
    elif [[ -e "$EXTRACT_DIR$path" ]]; then
        echo "⚠️  $desc exists but not executable: $path"
        return 1
    else
        echo "❌ MISSING $desc: $path"
        return 1
    fi
}

ERRORS=0

# Koii Settings
echo "## Koii Settings"
check_executable "/usr/bin/koii-settings" "Koii Settings executable" || ((ERRORS++))
check_file "/usr/share/applications/org.koii.Settings.desktop" "Koii Settings desktop file" || ((ERRORS++))
check_file "/usr/share/glib-2.0/schemas/org.koii.Settings.gschema.xml" "Koii Settings GSettings schema" || ((ERRORS++))
check_file "/usr/share/icons/hicolor/scalable/apps/org.koii.Settings.svg" "Koii Settings icon" || ((ERRORS++))
echo ""

# Koii Command
echo "## Koii Command Line"
check_executable "/usr/local/bin/koii" "Koii CLI command" || ((ERRORS++))
check_file "/opt/aios/src/koii_cli.py" "Koii CLI Python module" || ((ERRORS++))
echo ""

# AI Browser
echo "## AI Browser"
check_file "/usr/share/applications/koii-ai-browser.desktop" "AI Browser desktop file" || ((ERRORS++))
check_executable "/opt/aios/scripts/launch-ai-browser.sh" "AI Browser launcher" || ((ERRORS++))
check_file "/opt/aios/electron" "Electron directory" || ((ERRORS++))
check_file "/opt/aios/electron/package.json" "Electron package.json" || ((ERRORS++))
echo ""

# Core AIOS
echo "## Core AIOS Components"
check_file "/opt/aios" "AIOS installation directory" || ((ERRORS++))
check_file "/opt/aios/src" "AIOS source directory" || ((ERRORS++))
check_file "/opt/aios/src/koii_os" "Koii OS Python package" || ((ERRORS++))
echo ""

# Python dependencies
echo "## Python Environment"
if [[ -x "$EXTRACT_DIR/usr/bin/python3" ]]; then
    echo "✅ Python 3 installed"
    # Check for key Python packages
    if chroot "$EXTRACT_DIR" python3 -c "import gi" 2>/dev/null; then
        echo "✅ PyGObject (gi) available"
    else
        echo "❌ PyGObject (gi) NOT available"
        ((ERRORS++))
    fi
else
    echo "❌ Python 3 NOT installed"
    ((ERRORS++))
fi
echo ""

# Desktop integration
echo "## Desktop Integration"
if [[ -f "$EXTRACT_DIR/usr/share/applications/org.koii.Settings.desktop" ]]; then
    if grep -q "X-GNOME-Settings-Panel=koii-settings" "$EXTRACT_DIR/usr/share/applications/org.koii.Settings.desktop"; then
        echo "✅ Koii Settings registered as GNOME Settings panel"
    else
        echo "⚠️  Koii Settings desktop file missing Settings panel registration"
    fi
fi
echo ""

# Cleanup
echo "Cleaning up..."
rm -rf "$WORKDIR"

echo ""
echo "=== Summary ==="
if [[ $ERRORS -eq 0 ]]; then
    echo "✅ All components verified successfully!"
    echo ""
    echo "The ISO should work correctly with:"
    echo "  - Koii Settings in GNOME Settings"
    echo "  - AI Browser in applications menu"
    echo "  - 'koii' command in terminal"
    exit 0
else
    echo "❌ Found $ERRORS missing or incorrect components"
    echo ""
    echo "The ISO may not work correctly. Please rebuild with fixes."
    exit 1
fi

# Made with Bob
