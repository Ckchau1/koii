# AIOS ISO Build - Quick Start Guide

## Prerequisites

- Ubuntu 24.04 LTS (or compatible Debian-based system)
- 20GB free disk space
- 4GB RAM minimum (8GB recommended)
- Sudo privileges
- Internet connection

## One-Command Build

```bash
sudo ./scripts/build_ubuntu_aios_iso_rootless.sh
```

That's it! The script will:
1. Install all required dependencies
2. Configure live-build
3. Integrate AIOS components
4. Build the ISO (40-90 minutes)
5. Output: `build/AIOS-Ubuntu-24.04.2-live.iso`

## What Gets Built

Your custom ISO includes:

✅ **Ubuntu 24.04 Desktop** - Full GNOME desktop environment
✅ **Koii AIOS Core** - Complete AI Operating System
✅ **Koii Agent** - Distributed computing runtime
✅ **AI Browser** - Electron-based browser with automation
✅ **Task Scheduler** - Automated task execution
✅ **CLI Tools** - `koii` command-line interface
✅ **Docker Integration** - Container runtime pre-configured
✅ **System Services** - Auto-start systemd services
✅ **Desktop Shortcuts** - One-click access to AIOS tools

## Testing Your ISO

### Option 1: QEMU (Fastest)

```bash
qemu-system-x86_64 \
  -cdrom build/AIOS-Ubuntu-24.04.2-live.iso \
  -m 4G \
  -enable-kvm \
  -cpu host \
  -smp 2 \
  -vga virtio
```

### Option 2: VirtualBox

1. Create new VM: "Ubuntu 64-bit"
2. RAM: 4GB, CPUs: 2
3. Attach ISO to optical drive
4. Start VM

### Option 3: Physical USB

```bash
# Find your USB device
lsblk

# Write ISO (replace sdX with your device)
sudo dd if=build/AIOS-Ubuntu-24.04.2-live.iso \
        of=/dev/sdX \
        bs=4M \
        status=progress \
        conv=fsync

# Safely eject
sync
sudo eject /dev/sdX
```

## Installation

1. **Boot from ISO/USB**
2. **Select "Install Ubuntu"**
3. **Follow the wizard**:
   - Language: English (or your preference)
   - Keyboard: US (or your layout)
   - Installation type: Erase disk (or manual)
   - User: Create your account
4. **Wait for installation** (10-20 minutes)
5. **Reboot**
6. **AIOS auto-configures** on first boot!

## First Boot - Getting Started

### Check AIOS Installation

```bash
# Verify AIOS is installed
koii --version

# Show help
koii --help

# Check services
systemctl status aios-agent
systemctl status aios-browser
systemctl status aios-scheduler
```

### Start AIOS Services

```bash
# Start all services
sudo systemctl start aios-agent
sudo systemctl start aios-browser
sudo systemctl start aios-scheduler

# Enable auto-start on boot
sudo systemctl enable aios-agent
sudo systemctl enable aios-browser
sudo systemctl enable aios-scheduler
```

### Launch AI Browser

**From Desktop**: Click "Koii AI Browser" icon

**From Terminal**:
```bash
/opt/aios/electron/start-browser.sh
```

### Open Control Center

```bash
koii dashboard
```

### Run Your First Task

```bash
# List available tasks
koii task list

# Run a task
koii task run <task-name>

# Check task status
koii task status
```

## Directory Structure

After installation, AIOS files are located at:

```
/opt/aios/                    # Main application
├── src/                      # Python source code
├── electron/                 # AI Browser
├── scripts/                  # CLI tools
├── requirements.txt          # Python dependencies
└── .venv/                    # Python virtual environment

/var/lib/aios/                # Data directory
├── data/                     # Application data
├── logs/                     # Log files
├── cache/                    # Cache files
└── workspace/                # Task workspace

/etc/systemd/system/          # System services
├── aios-agent.service
├── aios-browser.service
└── aios-scheduler.service

/usr/share/applications/      # Desktop integration
├── aios-browser.desktop
└── aios-control.desktop
```

## Common Commands

```bash
# Agent management
koii agent start              # Start agent
koii agent stop               # Stop agent
koii agent status             # Check status
koii agent logs               # View logs

# Task management
koii task list                # List tasks
koii task run <name>          # Run task
koii task stop <name>         # Stop task
koii task status              # Task status

# System management
koii dashboard                # Open control center
koii config show              # Show configuration
koii config set <key> <val>   # Set config value
koii logs                     # View all logs

# Service management
sudo systemctl start aios-agent
sudo systemctl stop aios-agent
sudo systemctl restart aios-agent
sudo systemctl status aios-agent
journalctl -u aios-agent -f   # Follow logs
```

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
sudo systemctl status docker
sudo systemctl start docker

# Check permissions
sudo usermod -aG docker $USER
# Log out and back in for group changes

# Reinstall if needed
sudo apt install --reinstall aios-core
```

### Python Environment Issues

```bash
# Recreate virtual environment
cd /opt/aios
sudo rm -rf .venv
sudo -u aios python3 -m venv .venv
sudo -u aios .venv/bin/pip install -r requirements.txt
```

### Browser Won't Launch

```bash
# Reinstall dependencies
cd /opt/aios/electron
sudo -u aios npm install

# Check display
echo $DISPLAY  # Should show :0 or similar

# Run manually
cd /opt/aios/electron
npm start
```

### Check Logs

```bash
# System logs
journalctl -u aios-agent -n 100
journalctl -u aios-browser -n 100
journalctl -u aios-scheduler -n 100

# Application logs
tail -f /var/lib/aios/logs/*.log

# Build logs (if building ISO)
tail -f build/build_*.log
```

## Advanced Usage

### Custom Configuration

Edit `/opt/aios/aios-config.yaml`:

```yaml
agent:
  enabled: true
  auto_start: true
  log_level: debug

browser:
  headless: false
  user_agent: "Custom-Agent"

scheduler:
  max_concurrent_tasks: 10
```

### Development Mode

```bash
# Activate Python environment
cd /opt/aios
source .venv/bin/activate

# Run directly
python -m src.koii_cli agent start

# Install additional packages
pip install <package-name>
```

### Docker Integration

```bash
# List AIOS containers
docker ps -a | grep aios

# View container logs
docker logs <container-id>

# Access container
docker exec -it <container-id> bash
```

## Security Notes

### Change Default Password

If you used the preseed installation with default credentials:

```bash
# Default: aios / aios123
# CHANGE IMMEDIATELY:
passwd
```

### Firewall Configuration

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (if needed)
sudo ufw allow ssh

# Check status
sudo ufw status
```

### Docker Security

Remember: Docker access = root privileges!

```bash
# Only add trusted users to docker group
sudo usermod -aG docker username
```

## Getting Help

- **Documentation**: https://koii.network/docs
- **Community**: https://koii.network/community
- **Issues**: https://github.com/koii-network/AIOS/issues
- **Discord**: https://discord.gg/koii

## Next Steps

1. ✅ Build ISO
2. ✅ Test in VM
3. ✅ Install on hardware
4. ✅ Start services
5. 🚀 Start building with AIOS!

---

**Need more details?** See `config/BUILD_SYSTEM_README.md` for complete documentation.