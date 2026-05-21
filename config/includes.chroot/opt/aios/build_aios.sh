#!/usr/bin/env bash
set -euo pipefail

echo "=== AIOS Clean Build Started ==="
echo "Current directory: $(pwd)"
echo "This will take 40-90 minutes. Please wait..."

# 安裝工具
sudo apt update
sudo apt install -y live-build debootstrap squashfs-tools xorriso gnupg curl git rsync

# live-build 設定
lb config \
  --distribution noble \
  --architecture amd64 \
  --binary-images iso-hybrid \
  --debian-installer none \
  --bootappend-live "quiet splash vt.handoff=7" \
  --archive-areas "main restricted universe multiverse" \
  --apt-recommends false \
  --iso-volume "AIOS_UBUNTU_24_04" \
  --iso-preparer "Koii AIOS Builder" \
  --memtest none

# 套件清單
mkdir -p config/package-lists
cat > config/package-lists/aios.list.chroot << 'PKGS'
ubuntu-desktop-minimal
gnome-session gdm3
python3 python3-pip git curl docker.io docker-compose-plugin whiptail
PKGS

# 複製你的 AIOS 所有檔案（最重要的部分）
mkdir -p config/includes.chroot/opt/aios
rsync -a --exclude='.git' --exclude='.venv' --exclude='build' --exclude='data' \
  /mnt/c/Users/riven/Desktop/AIOS/ config/includes.chroot/opt/aios/ 2>/dev/null || true

echo "=== Starting real ISO build now... ==="
sudo lb build

# 完成後複製 ISO
if [[ -f live-image-amd64.hybrid.iso ]]; then
  mkdir -p /mnt/c/Users/riven/Desktop/AIOS/build
  mv live-image-amd64.hybrid.iso /mnt/c/Users/riven/Desktop/AIOS/build/AIOS-Ubuntu-24.04.2-rootless-live.iso
  echo "✅ BUILD SUCCESS!"
  echo "ISO 位置：/mnt/c/Users/riven/Desktop/AIOS/build/AIOS-Ubuntu-24.04.2-rootless-live.iso"
  ls -lh /mnt/c/Users/riven/Desktop/AIOS/build/
else
  echo "❌ Build failed"
fi
