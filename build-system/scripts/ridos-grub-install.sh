#!/bin/bash
# RIDOS GRUB Installer v4 - supports BIOS and EFI
LOG="/tmp/ridos-grub.log"
exec > "$LOG" 2>&1
echo "=== RIDOS GRUB Install v4 $(date) ==="

# Find Calamares mount point
T=""
for d in /tmp/calamares-root-*; do
    if [ -d "$d" ] && [ -d "$d/etc" ] && [ -d "$d/usr" ]; then
        T="$d"; echo "Found: $T"; break
    fi
done

if [ -z "$T" ]; then
    while read dev mnt fs opts dump pass; do
        if [ "$mnt" != "/" ] && [ "$mnt" != "none" ] && \
           [ -d "$mnt/etc" ] && [ -d "$mnt/usr" ] && [ -d "$mnt/boot" ]; then
            T="$mnt"; echo "Found via mounts: $T"; break
        fi
    done < /proc/mounts
fi

[ -z "$T" ] && echo "FATAL: No target" && exit 1
echo "Target: $T"

# Find disk
DEV=$(grep " $T " /proc/mounts | awk '{print $1}' | head -1)
echo "Device: $DEV"

# Strip partition to get disk
if echo "$DEV" | grep -q "nvme"; then
    DISK=$(echo "$DEV" | sed 's/p[0-9]*$//')
else
    DISK=$(echo "$DEV" | sed 's/[0-9]*$//')
fi
[ ! -b "$DISK" ] && DISK="/dev/sda"
echo "Disk: $DISK"

# Mount filesystems
mount --bind /dev     "$T/dev"
mount --bind /dev/pts "$T/dev/pts"
mount --bind /proc    "$T/proc"
mount --bind /sys     "$T/sys"
mount --bind /sys/firmware/efi/efivars "$T/sys/firmware/efi/efivars" 2>/dev/null || true

# Install BIOS GRUB
echo "Installing BIOS GRUB..."
chroot "$T" grub-install --target=i386-pc --recheck --force "$DISK"
echo "BIOS grub-install: $?"

# Install EFI GRUB if EFI partition exists
if [ -d "/sys/firmware/efi" ]; then
    echo "EFI system detected - installing EFI GRUB..."
    mkdir -p "$T/boot/efi"
    # Find EFI partition
    EFI_PART=$(fdisk -l "$DISK" 2>/dev/null | grep "EFI" | awk '{print $1}' | head -1)
    if [ -n "$EFI_PART" ]; then
        mount "$EFI_PART" "$T/boot/efi" 2>/dev/null || true
        chroot "$T" grub-install --target=x86_64-efi \
            --efi-directory=/boot/efi \
            --bootloader-id=RIDOS \
            --recheck 2>/dev/null || true
        echo "EFI grub-install done"
    fi
fi

# Generate GRUB config
echo "Running update-grub..."
chroot "$T" update-grub
echo "update-grub: $?"

# Unmount
umount "$T/sys/firmware/efi/efivars" 2>/dev/null || true
umount "$T/sys"     2>/dev/null || true
umount "$T/proc"    2>/dev/null || true
umount "$T/dev/pts" 2>/dev/null || true
umount "$T/dev"     2>/dev/null || true

echo "=== DONE ==="
cat "$LOG"
exit 0
