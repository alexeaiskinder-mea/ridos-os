#!/bin/bash
# RIDOS OS live-build configuration script
cd "$(dirname "$0")/.."
sudo lb config \
  --distribution bookworm \
  --architectures amd64 \
  --mirror-bootstrap "http://deb.debian.org/debian/" \
  --archive-areas "main contrib non-free non-free-firmware" \
  --binary-images iso-hybrid \
  --debian-installer false \
  --linux-packages "linux-image" \
  --linux-flavours amd64 \
  --apt-recommends false
