#!/bin/bash
# This script is called during build to inject apt config into the chroot
# before lb_chroot_linux-image runs
LB_INSTALL="/usr/lib/live/build/lb_chroot_install-packages"
if [ -f "$LB_INSTALL" ]; then
  sudo sed -i '2i mkdir -p "${CHROOT}/etc/apt/apt.conf.d" 2>/dev/null; printf "Acquire::IndexTargets::deb::Contents-deb::DefaultEnabled false;\\n" > "${CHROOT}/etc/apt/apt.conf.d/99no-contents" 2>/dev/null' "$LB_INSTALL"
  echo "Patched $LB_INSTALL"
fi
