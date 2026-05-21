cd ~
rm -rf ai-os-build
mkdir ai-os-build
cd ai-os-build
cat > build_aios.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "=== AIOS Build Started ==="
echo "Current path: $(pwd)"
sudo apt update && sudo apt install -y live-build debootstrap squashfs-tools xorriso gnupg curl git rsync
lb config --distribution noble --architecture amd64 --binary-images iso-hybrid --debian-installer none --bootappend-live "quiet splash vt.handoff=7" --archive-areas "main restricted universe multiverse" --apt-recommends false --iso-volume "AIOS_UBUNTU_24_04" --iso-preparer "Koii AIOS"
mkdir -p config/package-lists
cat > config/package-lists/aios.list.chroot << 'PKGS'
ubuntu-desktop-minimal gnome-session gdm3 python3 python3-pip git curl docker.io whiptail
PKGS
mkdir -p config/includes.chroot/opt/aios
rsync -a --exclude='.git' --exclude='.venv' --exclude='build' --exclude='data' /mnt/c/Users/riven/Desktop/AIOS/ config/includes.chroot/opt/aios/ 2>/dev/null || true
echo "=== Starting real build (long time) ==="
sudo lb build
if [[ -f live-image-amd64.hybrid.iso ]]; then
  mkdir -p /mnt/c/Users/riven/Desktop/AIOS/build
  mv live-image-amd64.hybrid.iso /mnt/c/Users/riven/Desktop/AIOS/build/AIOS-Ubuntu-24.04.2-rootless-live.iso
  echo "✅ SUCCESS! ISO created"
  ls -lh /mnt/c/Users/riven/Desktop/AIOS/build/
else
  echo "❌ Build failed"
fi
EOF
chmod +x build_aios.sh
echo "✅ Build script created at $(pwd)/build_aios.sh"