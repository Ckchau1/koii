# AIOS Ubuntu ISO Build System

Complete live-build configuration for creating a custom Ubuntu 24.04 ISO with integrated Koii AIOS components.

## Overview

This build system creates a bootable Ubuntu ISO that includes:

- **Koii AIOS Core**: Complete AI Operating System framework
- **Koii Agent Runtime**: Distributed computing agent
- **AI Browser**: Electron-based browser with automation
- **Task Scheduler**: Automated task execution engine
- **Command-line Tools**: `koii` CLI for system management
- **System Integration**: Systemd services, desktop shortcuts, auto-configuration

## Architecture

### Directory Structure

```
config/
├── package-lists/              # APT packages to install
│   └── aios.list.chroot       # AIOS package list
├── packages.chroot/           # Custom Debian packages
│   └── aios-core_1.0.0_all/  # AIOS Debian package
│       └── DEBIAN/
│           ├── control        # Package metadata
│           ├── postinst       # Post-installation script
│           └── prerm          # Pre-removal script
├── includes.chroot/           # Files copied to live system
│   ├── etc/systemd/system/   # Systemd service files
│   │   ├── aios-agent.service
│   │   ├── aios-browser.service
│   │   └── aios-scheduler.service
│   ├── usr/share/applications/ # Desktop integration
│   │   ├── aios-browser.desktop
│   │   └── aios-control.desktop
│   └── opt/aios/              # AIOS application files
├── hooks/live/                # Build-time hooks (run in chroot)
│   ├── 0100-install-aios-package.hook.chroot
│   └── 0200-configure-aios-environment.hook.chroot
├── includes.installer/        # Files for installer
│   └── usr/lib/finish-install.d/
│       └── 99aios-setup       # Post-install configuration
└── preseed/                   # Automated installation
    └── aios.preseed          # Preseed configuration
```

## Build Process

### Phase 1: Preparation
1. Install build dependencies (live-build, debootstrap, etc.)
2. Configure live-build with Ubuntu 24.04 Noble base
3. Set up package lists and repositories

### Phase 2: File Integration
1. Copy AIOS source code to `includes.chroot/opt/aios/`
2. Copy systemd services to `includes.chroot/etc/systemd/system/`
3. Copy desktop files to `includes.chroot/usr/share/applications/`
4. Build AIOS Debian package (optional)

### Phase 3: Chroot Hooks
Hooks run inside the chroot environment during build:

**0100-install-aios-package.hook.chroot**:
- Builds and installs AIOS Debian package
- Sets file permissions
- Enables systemd services

**0200-configure-aios-environment.hook.chroot**:
- Installs Node.js for Electron browser
- Creates Python virtual environment
- Installs Python dependencies
- Installs npm packages for browser
- Configures Docker
- Creates default configuration files
- Sets up GNOME desktop integration

### Phase 4: ISO Generation
1. Create squashfs filesystem
2. Generate bootloader configuration
3. Build ISO image with xorriso
4. Calculate checksums

### Phase 5: Verification
1. Verify ISO file exists
2. Calculate MD5 checksum
3. Generate build information file

## Components

### Debian Package (aios-core)

**Package**: aios-core_1.0.0_all.deb

**Contents**:
- `/opt/aios/`: Complete AIOS application
- `/usr/local/bin/koii`: CLI tool symlink
- Systemd service files
- Desktop integration files

**Dependencies**:
- python3 (>= 3.10)
- python3-pip, python3-venv
- git, curl
- docker.io, docker-compose-plugin
- nodejs (>= 18), npm
- chromium-browser
- sqlite3, whiptail

**Post-installation** (postinst):
- Creates `aios` system user
- Sets up data directories in `/var/lib/aios/`
- Creates Python virtual environment
- Installs Python dependencies
- Installs Electron browser dependencies
- Enables systemd services
- Creates desktop shortcuts

### Systemd Services

**aios-agent.service**:
- Runs Koii agent runtime
- User: aios
- Auto-restart on failure
- Depends on: docker.service

**aios-browser.service**:
- Runs Electron AI browser
- User: aios
- Requires DISPLAY environment
- Depends on: aios-agent.service

**aios-scheduler.service**:
- Runs task scheduler
- User: aios
- Manages automated tasks
- Depends on: aios-agent.service

### Desktop Integration

**aios-browser.desktop**:
- Launches AI Browser
- Category: Network, WebBrowser
- Icon: /opt/aios/electron/icon.png

**aios-control.desktop**:
- Opens AIOS Control Center
- Category: System, Settings
- Runs: koii dashboard

### Installer Integration

**99aios-setup** (finish-install hook):
- Runs at end of Ubuntu installation
- Configures AIOS for installed system
- Creates user accounts
- Sets up Python environment
- Installs dependencies
- Enables services
- Creates desktop shortcuts for first user
- Generates welcome documentation

### Preseed Configuration

**aios.preseed**:
- Automated installation configuration
- Default user: aios / aios123
- Automatic partitioning with LVM
- Package selection
- Post-installation commands
- Service enablement

## Usage

### Building the ISO

```bash
cd /path/to/AIOS
sudo ./scripts/build_ubuntu_aios_iso_rootless.sh
```

**Requirements**:
- Ubuntu 24.04 or compatible
- 20GB free disk space
- 4GB RAM minimum
- sudo privileges

**Build Time**: 40-90 minutes depending on system

**Output**:
- ISO: `build/AIOS-Ubuntu-24.04.2-live.iso`
- Checksum: `build/AIOS-Ubuntu-24.04.2-live.iso.md5`
- Build info: `build/build-info.txt`
- Build log: `build/build_YYYYMMDD_HHMMSS.log`

### Testing the ISO

**In QEMU**:
```bash
qemu-system-x86_64 \
  -cdrom build/AIOS-Ubuntu-24.04.2-live.iso \
  -m 4G \
  -enable-kvm \
  -cpu host \
  -smp 2
```

**In VirtualBox**:
1. Create new VM (Ubuntu 64-bit)
2. Allocate 4GB RAM, 2 CPUs
3. Attach ISO as optical drive
4. Boot and test

### Installing from ISO

**Write to USB**:
```bash
sudo dd if=build/AIOS-Ubuntu-24.04.2-live.iso \
        of=/dev/sdX \
        bs=4M \
        status=progress \
        conv=fsync
```

**Boot and Install**:
1. Boot from USB
2. Select "Install Ubuntu"
3. Follow installation wizard
4. AIOS will be automatically configured
5. Reboot into installed system

### First Boot

After installation:

```bash
# Check AIOS status
koii --help

# Start services
sudo systemctl start aios-agent
sudo systemctl start aios-browser
sudo systemctl start aios-scheduler

# Check service status
systemctl status aios-agent

# View logs
journalctl -u aios-agent -f

# Open control center
koii dashboard
```

## Customization

### Adding Packages

Edit `config/package-lists/aios.list.chroot`:
```
# Add your packages
your-package-name
another-package
```

### Modifying Services

Edit service files in `config/includes.chroot/etc/systemd/system/`:
- Change user, environment variables, or commands
- Add dependencies or ordering

### Custom Hooks

Create new hooks in `config/hooks/live/`:
- Name format: `NNNN-description.hook.chroot`
- Must be executable (`chmod +x`)
- Runs in chroot environment
- Use `in-target` for commands in installed system

### Preseed Customization

Edit `config/preseed/aios.preseed`:
- Change default user/password
- Modify partitioning scheme
- Add/remove packages
- Customize post-installation commands

## Troubleshooting

### Build Fails

**Check logs**:
```bash
tail -f build/build_*.log
```

**Common issues**:
- Insufficient disk space: Need 20GB free
- Network issues: Check internet connection
- Permission errors: Run with sudo
- Package conflicts: Update package lists

### ISO Won't Boot

**Verify ISO**:
```bash
md5sum build/AIOS-Ubuntu-24.04.2-live.iso
cat build/AIOS-Ubuntu-24.04.2-live.iso.md5
```

**Check USB write**:
```bash
sudo fdisk -l /dev/sdX
```

### Services Not Starting

**Check status**:
```bash
systemctl status aios-agent
journalctl -u aios-agent -n 50
```

**Common issues**:
- Docker not running: `sudo systemctl start docker`
- Permission errors: Add user to docker group
- Missing dependencies: Reinstall package

### Python Environment Issues

**Recreate venv**:
```bash
cd /opt/aios
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Development

### Testing Changes

1. Modify files in `config/`
2. Rebuild ISO
3. Test in VM
4. Iterate

### Quick Rebuild

To rebuild without cleaning:
```bash
cd /tmp/aios-live-build
sudo lb clean
sudo lb build
```

### Debugging Hooks

Add debug output to hooks:
```bash
set -x  # Enable debug mode
echo "Debug: Current directory: $(pwd)"
ls -la
```

## Security Considerations

### Default Credentials

**IMPORTANT**: Change default password immediately after installation!

Default user: `aios`
Default password: `aios123`

```bash
passwd  # Change password
```

### Service Security

Services run as `aios` user with limited privileges:
- NoNewPrivileges=true
- PrivateTmp=true
- ProtectSystem=strict
- ReadWritePaths limited

### Docker Security

Add users to docker group carefully:
```bash
sudo usermod -aG docker username
```

Docker access = root-equivalent privileges!

## Contributing

To contribute improvements:

1. Test changes thoroughly
2. Document modifications
3. Update this README
4. Submit pull request

## License

See main project LICENSE file.

## Support

- Documentation: https://koii.network/docs
- Issues: https://github.com/koii-network/AIOS/issues
- Community: https://koii.network/community