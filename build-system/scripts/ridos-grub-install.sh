#!/bin/bash
# RIDOS GRUB Installer v3
# Runs on LIVE system during Calamares installation
# Finds target, mounts /dev /proc /sys, installs GRUB properly

LOG="/tmp/ridos-grub.log"
exec > "$LOG" 2>&1
echo "=== RIDOS GRUB Install v3 $(date) ==="

# Step 1: Find Calamares mount point
T=""
for d in /tmp/calamares-root-*; do
    if [ -d "$d" ] && [ -d "$d/etc" ] && [ -d "$d/usr" ]; then
        T="$d"
        echo "Found via glob: $T"
        break
    fi
done

# Step 2: Scan all mounts if not found
if [ -z "$T" ]; then
    echo "Glob failed, scanning /proc/mounts..."
    while read dev mnt fs opts dump pass; do
        if [ "$mnt" != "/" ] && \
           [ "$mnt" != "none" ] && \
           [ -d "$mnt/etc" ] && \
           [ -d "$mnt/usr" ] && \
           [ -d "$mnt/boot" ]; then
            T="$mnt"
            echo "Found via mounts: $T"
            break
        fi
    done < /proc/mounts
fi

if [ -z "$T" ]; then
    echo "FATAL: Cannot find target mount point"
    cat "$LOG"
    exit 1
fi

echo "Target: $T"

# Step 3: Find the target DISK (not partition)
DEV=$(grep " $T " /proc/mounts | awk '{print $1}' | head -1)
echo "Device: $DEV"

# Strip partition number to get disk
DISK=$(echo "$DEV" | sed 's/[0-9]*$//' | sed 's/p$//')
# Handle nvme (nvme0n1p1 -> nvme0n1)
if echo "$DEV" | grep -q "nvme"; then
    DISK=$(echo "$DEV" | sed 's/p[0-9]*$//')
fi

echo "Disk: $DISK"

if [ -z "$DISK" ] || [ ! -b "$DISK" ]; then
    echo "WARNING: Could not detect disk, trying /dev/sda"
    DISK="/dev/sda"
fi

# Step 4: Mount /dev /proc /sys
echo "Mounting filesystems..."
mount --bind /dev     "$T/dev"     && echo "OK /dev"     || echo "WARN /dev"
mount --bind /dev/pts "$T/dev/pts" && echo "OK /dev/pts" || echo "WARN /dev/pts"
mount --bind /proc    "$T/proc"    && echo "OK /proc"    || echo "WARN /proc"
mount --bind /sys     "$T/sys"     && echo "OK /sys"     || echo "WARN /sys"

# Step 5: Install GRUB inside chroot
echo "Running grub-install on $DISK..."
chroot "$T" grub-install --target=i386-pc --recheck --force "$DISK"
R=$?
echo "grub-install exit code: $R"

# Step 6: Generate GRUB config
echo "Running update-grub..."
chroot "$T" update-grub
echo "update-grub done"

# Step 7: Unmount
echo "Unmounting..."
umount "$T/sys"     2>/dev/null || true
umount "$T/proc"    2>/dev/null || true
umount "$T/dev/pts" 2>/dev/null || true
umount "$T/dev"     2>/dev/null || true

echo "=== DONE exit code: $R ==="
cat "$LOG"
exit $R
