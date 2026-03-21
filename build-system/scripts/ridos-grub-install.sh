#!/bin/bash
# RIDOS GRUB Installer
# Runs on LIVE system during Calamares installation
LOG="/tmp/ridos-grub.log"
echo "=== RIDOS GRUB Install $(date) ===" > "$LOG"

# Find Calamares mount point
T=""
for d in /tmp/calamares-root-* /tmp/calamares-root /tmp/calamares /mnt/target; do
    if [ -d "$d" ] && [ -d "$d/boot" ] && [ -d "$d/etc" ]; then
        T="$d"
        break
    fi
done

# Scan all mounts
if [ -z "$T" ]; then
    while read dev mnt fs rest; do
        if [ "$mnt" != "/" ] && [ -d "$mnt/boot" ] && [ -d "$mnt/etc" ] && [ -d "$mnt/usr" ]; then
            T="$mnt"
            break
        fi
    done < /proc/mounts
fi

echo "Target: $T" >> "$LOG"

if [ -z "$T" ]; then
    echo "ERROR: No target found" >> "$LOG"
    cat "$LOG"
    exit 1
fi

mount --bind /dev     "$T/dev"     >> "$LOG" 2>&1 || true
mount --bind /dev/pts "$T/dev/pts" >> "$LOG" 2>&1 || true
mount --bind /proc    "$T/proc"    >> "$LOG" 2>&1 || true
mount --bind /sys     "$T/sys"     >> "$LOG" 2>&1 || true

echo "Running grub-install..." >> "$LOG"
chroot "$T" grub-install --target=i386-pc --recheck --force /dev/sda >> "$LOG" 2>&1
R=$?
echo "grub-install exit: $R" >> "$LOG"
chroot "$T" update-grub >> "$LOG" 2>&1
umount "$T/sys" "$T/proc" "$T/dev/pts" "$T/dev" >> "$LOG" 2>&1 || true
cat "$LOG"
exit $R
