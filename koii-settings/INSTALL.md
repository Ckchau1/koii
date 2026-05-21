# Koii Settings Installation Guide

This guide covers building and installing Koii Settings on Ubuntu 24.04 and compatible systems.

## Prerequisites

### Required Packages

```bash
sudo apt update
sudo apt install -y \
    meson \
    ninja-build \
    python3 \
    python3-gi \
    gir1.2-gtk-4.0 \
    gir1.2-adw-1 \
    gir1.2-secret-1 \
    libsecret-1-0 \
    libgtk-4-dev \
    libadwaita-1-dev \
    libsecret-1-dev \
    gettext \
    appstream \
    desktop-file-utils
```

### Optional Packages (for development)

```bash
sudo apt install -y \
    python3-pytest \
    python3-pylint \
    python3-black
```

## Building from Source

### 1. Clone or Extract the Source

If you're building from the AIOS repository:

```bash
cd /path/to/AIOS/koii-settings
```

### 2. Build the Application

```bash
# Make build script executable
chmod +x scripts/build.sh

# Run the build
./scripts/build.sh
```

Or manually:

```bash
# Setup build directory
meson setup build --prefix=/usr

# Compile
meson compile -C build

# Run tests (optional)
meson test -C build
```

### 3. Install

```bash
# Install system-wide (requires root)
sudo meson install -C build

# Run post-installation script
sudo chmod +x scripts/post-install.sh
sudo ./scripts/post-install.sh
```

## Installation for ISO Build

To include Koii Settings in the AIOS ISO:

### 1. Copy to ISO Build Directory

```bash
# From AIOS root directory
cp -r koii-settings /path/to/iso/build/root/opt/koii-settings
```

### 2. Add to ISO Build Script

Edit `scripts/build_ubuntu_aios_iso.sh` and add:

```bash
# Install Koii Settings
echo "Installing Koii Settings..."
cd /opt/koii-settings
meson setup build --prefix=/usr
meson compile -C build
DESTDIR="${ISO_ROOT}" meson install -C build

# Run post-install in chroot
chroot "${ISO_ROOT}" /opt/koii-settings/scripts/post-install.sh
```

### 3. Add to Package List

Add to `config/packages.chroot/aios.list.chroot`:

```
# Koii Settings dependencies
meson
ninja-build
python3-gi
gir1.2-gtk-4.0
gir1.2-adw-1
gir1.2-secret-1
libgtk-4-1
libadwaita-1-0
libsecret-1-0
```

## Verification

After installation, verify that Koii Settings is properly integrated:

### 1. Check Desktop File

```bash
desktop-file-validate /usr/share/applications/org.koii.Settings.desktop
```

### 2. Check GSettings Schema

```bash
gsettings list-schemas | grep org.koii.Settings
```

### 3. Check Icons

```bash
ls -la /usr/share/icons/hicolor/scalable/apps/org.koii.Settings.svg
ls -la /usr/share/icons/hicolor/symbolic/apps/org.koii.Settings-symbolic.svg
```

### 4. Launch the Application

```bash
# From command line
koii-settings

# Or from GNOME Settings
gnome-control-center
# Navigate to "Koii Settings" in the sidebar
```

## Uninstallation

To remove Koii Settings:

```bash
# Remove installed files
sudo ninja -C build uninstall

# Remove configuration (optional)
rm -rf ~/.config/koii-settings
sudo rm -rf /opt/aios/config/koii-settings.conf

# Remove GSettings data (optional)
gsettings reset-recursively org.koii.Settings
```

## Troubleshooting

### Application doesn't appear in GNOME Settings

1. Check if the desktop file is installed:
   ```bash
   ls -la /usr/share/applications/org.koii.Settings.desktop
   ```

2. Verify the desktop file has the correct category:
   ```bash
   grep "X-GNOME-Settings-Panel" /usr/share/applications/org.koii.Settings.desktop
   ```

3. Update desktop database:
   ```bash
   sudo update-desktop-database /usr/share/applications/
   ```

4. Restart GNOME Shell (X11):
   ```bash
   Alt+F2, type 'r', press Enter
   ```

### GSettings schema not found

```bash
# Recompile schemas
sudo glib-compile-schemas /usr/share/glib-2.0/schemas/

# Verify schema exists
gsettings list-schemas | grep koii
```

### Icons not showing

```bash
# Update icon cache
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor/

# Check icon theme
gsettings get org.gnome.desktop.interface icon-theme
```

### Import errors (gi.repository)

Make sure PyGObject is installed:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0
```

### Backend connection issues

If Koii Settings can't connect to the Koii OS backend:

1. Check if Koii OS is installed:
   ```bash
   ls -la /opt/aios/src/koii_os/
   ```

2. Verify Python path:
   ```bash
   python3 -c "import sys; print('\n'.join(sys.path))"
   ```

3. The application will run in standalone mode with mock data if the backend is unavailable.

## Development

### Running from Source (without installation)

```bash
# Set up environment
export PYTHONPATH="$PWD/src:$PYTHONPATH"
export XDG_DATA_DIRS="$PWD/data:$XDG_DATA_DIRS"

# Compile GSettings schema locally
mkdir -p data/glib-2.0/schemas
cp data/org.koii.Settings.gschema.xml data/glib-2.0/schemas/
glib-compile-schemas data/glib-2.0/schemas/

# Run the application
python3 src/main.py
```

### Code Style

Format code with Black:

```bash
black src/
```

Check with Pylint:

```bash
pylint src/
```

## Support

For issues and questions:

- GitHub Issues: https://github.com/koii-network/aios/issues
- Documentation: https://docs.koii.network/
- Community: https://discord.gg/koii

## License

Koii Settings is part of the AIOS project and is licensed under the same terms.
