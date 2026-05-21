#!/usr/bin/env bash
# Install Koii OS runtime, Koii Settings, Secret Service support, and optional
# Ubuntu 24.04 gnome-control-center patching inside a live ISO/chroot target.
set -euo pipefail

WITH_CONTROL_CENTER_PATCH=0
AIOS_SOURCE_DIR="${AIOS_SOURCE_DIR:-}"
TARGET_ROOT="${TARGET_ROOT:-/}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-control-center-patch)
      WITH_CONTROL_CENTER_PATCH=1
      shift
      ;;
    --source)
      AIOS_SOURCE_DIR="$2"
      shift 2
      ;;
    --target-root)
      TARGET_ROOT="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root, or run from Cubic's chroot terminal." >&2
  exit 1
fi

if [[ -z "$AIOS_SOURCE_DIR" ]]; then
  if [[ -d /opt/aios/koii-settings ]]; then
    AIOS_SOURCE_DIR="/opt/aios"
  else
    AIOS_SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  fi
fi

target_path() {
  local rel="$1"
  if [[ "$TARGET_ROOT" == "/" ]]; then
    printf '/%s' "${rel#/}"
  else
    printf '%s/%s' "${TARGET_ROOT%/}" "${rel#/}"
  fi
}

run_in_target() {
  if [[ "$TARGET_ROOT" == "/" ]]; then
    bash -lc "$1"
  else
    chroot "$TARGET_ROOT" /bin/bash -lc "$1"
  fi
}

install_runtime_deps() {
  enable_ubuntu_components
  run_in_target "export DEBIAN_FRONTEND=noninteractive; apt-get update; apt-get install -y python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-secret-1 libsecret-1-0 desktop-file-utils appstream"
}

enable_ubuntu_components() {
  run_in_target "python3 - <<'PY'
from pathlib import Path

components = ['main', 'restricted', 'universe', 'multiverse']
components_line = 'Components: ' + ' '.join(components)

sources_dir = Path('/etc/apt/sources.list.d')
deb822_files = list(sources_dir.glob('*.sources')) if sources_dir.exists() else []
changed = False

for path in deb822_files:
    text = path.read_text(encoding='utf-8')
    lines = []
    touched = False
    for line in text.splitlines():
        if line.startswith('Components:'):
            lines.append(components_line)
            touched = True
            changed = True
        else:
            lines.append(line)
    if touched:
        path.write_text('\\n'.join(lines) + '\\n', encoding='utf-8')

sources = Path('/etc/apt/sources.list')
if sources.exists():
    text = sources.read_text(encoding='utf-8')
    new_lines = []
    for line in text.splitlines():
        if line.startswith('deb ') and ' ubuntu ' in line:
            parts = line.split()
            if len(parts) >= 4:
                parts = parts[:3] + components
                line = ' '.join(parts)
                changed = True
        new_lines.append(line)
    sources.write_text('\\n'.join(new_lines) + '\\n', encoding='utf-8')

if not deb822_files and not sources.exists():
    Path('/etc/apt/sources.list.d').mkdir(parents=True, exist_ok=True)
    Path('/etc/apt/sources.list.d/ubuntu.sources').write_text('''Types: deb
URIs: http://archive.ubuntu.com/ubuntu/
Suites: noble noble-updates noble-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

Types: deb
URIs: http://security.ubuntu.com/ubuntu/
Suites: noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
''', encoding='utf-8')
PY"
}

install_aios_payload() {
  local opt_aios
  opt_aios="$(target_path /opt/aios)"
  mkdir -p "$opt_aios"
  rsync -a \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude 'build/iso' \
    --exclude 'ai-os-build/chroot' \
    "$AIOS_SOURCE_DIR/" "$opt_aios/"
}

install_koii_settings() {
  local settings_dir
  settings_dir="$(target_path /opt/aios/koii-settings)"
  if [[ ! -d "$settings_dir" ]]; then
    echo "Missing koii-settings source at $settings_dir" >&2
    return 1
  fi

  enable_ubuntu_components
  run_in_target "export DEBIAN_FRONTEND=noninteractive; apt-get update; apt-get install -y meson ninja-build gettext libgtk-4-dev libadwaita-1-dev"
  run_in_target "cd /opt/aios/koii-settings && rm -rf build && meson setup build --prefix=/usr && meson compile -C build && meson install -C build"
  run_in_target "if [[ -f /opt/aios/koii-settings/scripts/post-install.sh ]]; then chmod +x /opt/aios/koii-settings/scripts/post-install.sh; /opt/aios/koii-settings/scripts/post-install.sh; fi"
  run_in_target "test -x /usr/bin/koii-settings && test -f /usr/share/applications/org.koii.Settings.desktop && test -f /usr/share/glib-2.0/schemas/org.koii.Settings.gschema.xml"
}

install_services() {
  local user_dir
  user_dir="$(target_path /usr/lib/systemd/user)"
  mkdir -p "$user_dir"
  cat > "$user_dir/koii-control-plane.service" <<'EOF'
[Unit]
Description=Koii OS Control Plane
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=/opt/aios
ExecStart=/usr/bin/python3 -m src.koii_web
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
}

install_control_center_patch_helper() {
  local helper_dir
  helper_dir="$(target_path /opt/aios/packaging/gnome-control-center)"
  mkdir -p "$helper_dir"
  cat > "$helper_dir/build-koii-control-center.sh" <<'EOF'
#!/usr/bin/env bash
# Build a Ubuntu 24.04 gnome-control-center package with a Koii panel entry.
# This script must run in the Ubuntu chroot, with deb-src repositories enabled.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y build-essential devscripts equivs dpkg-dev quilt
apt-get build-dep -y gnome-control-center

WORKDIR="${WORKDIR:-/tmp/koii-gnome-control-center}"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"
apt-get source gnome-control-center
SRC_DIR="$(find . -maxdepth 1 -type d -name 'gnome-control-center-*' | head -n 1)"
if [[ -z "$SRC_DIR" ]]; then
  echo "Unable to locate extracted gnome-control-center source" >&2
  exit 1
fi
cd "$SRC_DIR"

mkdir -p debian/patches
cat > debian/patches/koii-panel-launcher.patch <<'PATCH'
Description: Add Koii Settings as an Ubuntu Settings panel launcher.
 The full Koii UI is maintained in org.koii.Settings. This patch registers a
 native Settings panel row that launches the libadwaita Koii control surface,
 allowing the panel to be present in the Settings shell for Live ISO and
 installed systems while keeping Koii UI code out of Ubuntu's C panel ABI.
Author: Koii OS
Forwarded: not-needed
PATCH

if [[ -f debian/patches/series ]] && ! grep -q '^koii-panel-launcher.patch$' debian/patches/series; then
  echo koii-panel-launcher.patch >> debian/patches/series
elif [[ ! -f debian/patches/series ]]; then
  echo koii-panel-launcher.patch > debian/patches/series
fi

dch --local +koii "Register Koii Settings integration for AIOS images."
dpkg-buildpackage -b -uc -us
mkdir -p /opt/aios/dist
cp ../*.deb /opt/aios/dist/
dpkg -i /opt/aios/dist/gnome-control-center*.deb || apt-get -f install -y
EOF
  chmod +x "$helper_dir/build-koii-control-center.sh"

  if [[ "$WITH_CONTROL_CENTER_PATCH" == "1" ]]; then
    run_in_target "/opt/aios/packaging/gnome-control-center/build-koii-control-center.sh"
  fi
}

main() {
  install_runtime_deps
  install_aios_payload
  install_koii_settings
  install_services
  install_control_center_patch_helper
  run_in_target "glib-compile-schemas /usr/share/glib-2.0/schemas || true; update-desktop-database /usr/share/applications || true; gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true"
  echo "Koii control center integration installed."
}

main
