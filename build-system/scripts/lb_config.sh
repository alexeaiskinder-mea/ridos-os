#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# RIDOS OS v1.1 — lb_config.sh
# Copyright (C) 2026 RIDOS OS Project — GPL v3
#
# Configures live-build for building RIDOS OS ISO
# Run this ONCE before lb build
# ═══════════════════════════════════════════════════════════════
set -e

R='\033[31m'; G='\033[32m'; Y='\033[33m'; C='\033[36m'
B='\033[1m';  X='\033[0m';  D='\033[2m'

[ "$EUID" -ne 0 ] && echo -e "${R}Run as root: sudo bash lb_config.sh${X}" && exit 1

echo -e "\n${R}${B}╔══════════════════════════════════════════════╗
║   RIDOS OS v1.1 — Configuring live-build    ║
║   Copyright (C) 2026 RIDOS OS Project       ║
╚══════════════════════════════════════════════╝${X}\n"

# ── Core live-build configuration ──────────────────────────────
lb config \
  --distribution bookworm \
  --arch amd64 \
  --archive-areas "main contrib non-free non-free-firmware" \
  \
  --bootloaders "grub-pc,grub-efi-amd64" \
  --uefi-secure-boot disable \
  --binary-images iso-hybrid \
  \
  --debian-installer false \
  --memtest none \
  --win32-loader false \
  \
  --iso-volume "RIDOS_OS_1.1" \
  --iso-publisher "RIDOS OS Project <https://github.com/ridos-os>" \
  --iso-application "RIDOS OS v1.1 - Retro Intelligent Desktop OS" \
  \
  --linux-packages "linux-image-amd64 linux-headers-amd64" \
  --linux-flavours amd64 \
  \
  --firmware-binary true \
  --firmware-chroot true \
  \
  --apt-recommends false \
  --apt-options "--yes -oAPT::Get::AllowUnauthenticated=true" \
  \
  --debootstrap-options "--include=apt-transport-https,ca-certificates,curl,gnupg"

echo -e "${G}✓ live-build configured${X}"
echo -e "${C}Next: sudo bash build-system/scripts/pre_build.sh${X}\n"
